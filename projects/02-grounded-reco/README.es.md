<!-- i18n-source-sha: 4d638209f1f9051775450456494c19fd1df96aea3f13cc5260e214ef93e4fbb7 -->

# Nivel 2: grounded-reco

> Read this in [English](./README.md).

Un pack de recomendación gobernado. Elige la mejor opción de un conjunto de candidatos, donde una recomendación equivocada o desactualizada sale cara. La decisión la toma código Python determinista. El modelo solo explica la decisión. Una evaluación determinista revisa el resultado antes de que llegue a un usuario, y se escribe un registro de auditoría detallado en cada ejecución. Este es el peldaño donde un pack de Huitzo deja de parecer una envoltura delgada sobre un modelo y empieza a parecer software gobernado que, además, usa un modelo.

**Aprenderás:** cómo mantener la decisión en Python y limitar al modelo a la prosa; cómo agregar una evaluación de guardia automática que retiene una mala respuesta antes de publicarla; cómo producir un registro de auditoría para cada generación; y cómo la Policy Card declara autonomía, nivel de auditoría y escalamiento para que la plataforma los haga cumplir.

**Tiempo:** unos quince minutos.

## Requisitos previos

- Python 3.11+
- La [CLI de Huitzo](https://github.com/Huitzo-Inc/huitzo-launcher) (opcional en este peldaño, se usa para ejecutar contra un Hub real)
- Primero el nivel [`hello-pack`](../00-hello-pack/), si aún no lo has hecho. Este pack asume que ya conoces el decorador `@command`, los argumentos y la salida tipados, y la regla de perfil-no-nombre-de-modelo.

## El escenario

Tienes un conjunto de opciones candidatas (piensa en proveedores, asignaciones, vendedores) y necesitas recomendar una. Cada candidato lleva unos cuantos números normalizados y una fecha que indica cuándo se actualizaron sus datos por última vez. El costo de una elección equivocada o desactualizada es real, así que una respuesta que suena segura construida sobre números rancios es peor que ninguna respuesta.

## Ejecútalo

```bash
cd pack
pip install -e ".[dev]"
pytest                  # pruebas sin conexión de este pack (lo que corre CI)
```

Deberías ver nueve pruebas en verde, sin red y sin modelo. No solo comprueban que el comando funciona; codifican el contrato de gobernanza: que la elección es determinista, que un resultado rancio o sin fundamento se retiene y se escala, y que cada ejecución queda auditada.

**Mira tú mismo el "ajá" del cambio de modelo, sin conexión:**

```bash
python -m grounded_reco.demo_model_swap
```

Ejecuta el comando `recommend` *real* bajo dos "modelos" simulados distintos y los imprime lado a lado. La elección, la compuerta de evaluación y la auditoría salen **idénticas al byte** — solo cambia la justificación de una frase. Esa es la historia de agnosticismo de modelo + gobernanza que no obtienes de un envoltorio fino sobre un SDK de LLM, mostrada en cinco segundos sin Hub. (La misma invariante queda fijada en CI por `tests/test_model_swap_demo.py`.)

## Qué hay dentro

```
pack/
  huitzo.yaml                      el manifiesto: identidad, un permiso, la Policy Card
  pyproject.toml                   dependencias y el punto de entrada del comando
  src/grounded_reco/
    commands/recommend.py          el comando: decide -> justifica -> evalúa -> audita
    evals.py                       la lógica de decisión determinista y la evaluación de guardia
    models/args.py                 entrada tipada (Candidate, RecommendArgs)
    models/output.py               salida tipada (Justification, ScoredCandidate, AuditRecord, Recommendation)
  tests/test_recommend.py          pruebas sin conexión que codifican el contrato de gobernanza
```

## Por qué esto no es una envoltura delgada sobre un LLM

Una envoltura delgada le pide al modelo que elija y luego devuelve lo que el modelo haya dicho. Este pack hace lo contrario. Cuatro propiedades lo hacen gobernado, y cada una es algo que una envoltura no tiene.

### 1. La decisión es determinista. El modelo no elige.

`evals.py` puntúa cada candidato con una fórmula fija y documentada, y los ordena. La cima del ranking es la elección. No hay modelo en ese camino.

```python
# score = 0.30 * (1 - cost) + 0.40 * quality + 0.30 * reliability
ranked = score_candidates(args.candidates)   # Python puro
pick = choose(ranked)                         # pick = ranked[0]
```

Como la puntuación son pesos fijos sobre los números del candidato, puedes predecir la elección a mano, y es reproducible: la misma entrada siempre produce la misma elección. Una de las pruebas lo demuestra directamente cambiando lo que devuelve el modelo (incluida una justificación que dice "elige kelp-llc en su lugar") y verificando que la elección nunca se mueve.

### 2. Al modelo solo se le pide explicar, y la explicación se revisa.

Después de que Python ha elegido, al modelo se le entrega la elección y los números y se le pide una justificación de una o dos frases. Se le indica, de forma explícita, que no proponga una opción distinta. El texto libre del objetivo se pasa dentro de etiquetas `<objective>...</objective>` con la instrucción de tratarlo como datos, no como instrucciones: una protección básica contra inyección de prompts para entradas no confiables.

```python
justification = await ctx.llm.complete(
    prompt=prompt,            # contiene la elección decidida + el ranking + el objetivo etiquetado
    profile="default",        # un perfil de capacidad, nunca un nombre de modelo
    schema=Justification,     # salida estructurada: el modelo devuelve prosa, nada más
)
```

El modelo devuelve prosa. No puede devolver una elección distinta, porque la elección no es uno de los campos que rellena.

### 3. Una evaluación automática protege el resultado antes de que llegue a un usuario.

Este es el corazón del nivel. Después de que el modelo responde y antes de que se devuelva cualquier cosa, `run_eval` aplica dos comprobaciones deterministas:

- **Frescura.** La elección lleva una fecha `as_of`. Si esos datos son más viejos que `freshness_days` (30 por defecto), o no tienen fecha, o tienen fecha en el futuro, la evaluación falla. Una recomendación rancia es la falla silenciosa clásica: parece segura y está equivocada porque las entradas se movieron por debajo.
- **Fundamento.** La justificación del modelo debe mencionar la elección por su nombre. Si no lo hace, la prosa no está fundamentada en la decisión (puede haberse desviado a otra opción o ser relleno genérico), y la evaluación falla.

Cuando la evaluación falla, el resultado se **retiene** y se **escala**:

```python
withheld = not eval_passed
escalated = not eval_passed
```

Un resultado retenido nunca se presenta como una recomendación segura. La `pick` y la `justification` pueden seguir adjuntas para que un revisor humano vea exactamente qué se generó, pero los indicadores `withheld` y `escalated` son la señal: no actúes sobre esto; una persona debe revisarlo. Así es como la evaluación bloquea una mala recomendación antes de que llegue a un usuario, en lugar de después.

### 4. Cada generación queda auditada.

La Policy Card declara `audit.level: detailed`. El comando lo honra construyendo un `AuditRecord` en cada ejecución: marca de tiempo, nivel de autonomía, número de candidatos, la elección, el resultado de la evaluación y cada hallazgo de la evaluación, devolviéndolo en la salida y registrándolo. Una ejecución que pasa y una que se retiene dejan el mismo rastro de evidencia, así que las fallas no son invisibles.

```python
audit = AuditRecord(
    timestamp=...,
    autonomy="suggest",
    candidate_count=len(args.candidates),
    pick=pick.name,
    eval_passed=eval_passed,
    eval_findings=eval_findings,
    escalated=escalated,
)
ctx.log.info(...)   # ejecución que pasa
ctx.log.warning(...)  # ejecución retenida
```

## La Policy Card

Abre `pack/huitzo.yaml` y busca el bloque `policy`. Esto no es documentación; la plataforma lo hace cumplir, y el cargador del manifiesto verifica que los `permissions` del pack sean un subconjunto de `policy.allowed_actions`.

```yaml
policy:
  autonomy: suggest                 # el pack propone; un humano dispone
  allowed_actions:
    - llm:complete
  data_scope:
    scope: tenant
  escalation:
    requires_human_approval:
      - recommend                   # este comando se escala a una persona
  audit:
    level: detailed                 # cada generación se audita en detalle
```

`autonomy: suggest` dice que este pack no actúa por su cuenta. `escalation` nombra a `recommend`, así que un resultado retenido tiene un destino definido: revisión humana. `audit.level: detailed` es el contrato que cumple el `AuditRecord`. El código y la Policy Card dicen lo mismo, y la plataforma obliga al pack a cumplirlo.

## El momento "cambia el modelo"

Como todo pack de Huitzo, este declara un requisito de capacidad, nunca un nombre de modelo:

```yaml
services:
  llm:
    required: true
    requirements:
      min_context: 8000
      capabilities:
        - structured_output
```

La decisión determinista, la evaluación y la auditoría no cambian cuando cambia el modelo. Cambia el perfil `default` de un modelo en la nube a uno local y la gobernanza es idéntica, porque nada de ella depende del modelo.

## Ejecútalo de verdad

> Reasígnalo primero: el ejemplo usa la org `@reef`, que no es tuya. Cambia `namespace:` en `huitzo.yaml` por una org que poseas y ejecuta `huitzo pack sync` antes de publicar. Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub).

Cuando tengas acceso anticipado a un Hub:

```bash
huitzo login
huitzo run @your-org/grounded-reco/recommend --args '{
  "candidates": [
    {"name": "reef-prime", "cost": 0.1, "quality": 0.9, "reliability": 0.95, "as_of": "2026-06-01"},
    {"name": "coral-co",   "cost": 0.5, "quality": 0.7, "reliability": 0.6,  "as_of": "2026-06-10"}
  ],
  "objective": "favorece la fiabilidad",
  "freshness_days": 30
}'
```

Cambia un `as_of` a una fecha bien en el pasado y ejecútalo de nuevo: la elección es la misma, pero el resultado regresa `withheld` y `escalated`, con un hallazgo de frescura en la auditoría. Eso es la guardia haciendo su trabajo.

## Siguiente

Ya tienes el patrón gobernado: decisión determinista, evaluación de guardia, auditoría, Policy Card. Los niveles superiores agregan almacenamiento, archivos y pipelines de varios pasos sobre exactamente esta columna vertebral.
