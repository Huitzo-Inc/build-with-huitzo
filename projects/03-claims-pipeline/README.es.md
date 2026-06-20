<!-- i18n-source-sha: ea0d02b9c2e3728e704fbf468668c5a4f573e13a6d7fba6c155d1e1d19d25413 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 3: claims-pipeline

> Read this in [English](./README.md).

Nautilus Mutual procesa siniestros de seguros todo el día. Un siniestro hay que leerlo, puntuar su riesgo y enrutarlo al desenlace correcto: aprobar de forma automática los pequeños y limpios, mandar los dudosos a una persona, escalar los riesgosos. Este pack lo hace como un **pipeline**: tres comandos pequeños, compuestos en orden, con la plataforma verificando los tipos del traspaso entre cada paso.

Este es el primer peldaño donde dejas de escribir un comando y empiezas a componer varios. La idea que hay que llevarse de aquí: **un flujo de trabajo en Huitzo es dato declarativo que el ejecutor valida, no código de pegamento que mantienes a mano.** Declaras las etapas en `huitzo.yaml`; cada etapa es un `@command` corriente que puedes probar y ejecutar por su cuenta.

> **Léelo como un entregable real, no un juguete.** Esta es la *forma* de la solución regulada que construyes sobre Huitzo y revendes: una decisión determinista en cada compuerta, un modelo confinado a prosa acotada que una evaluación verifica, un registro de auditoría completo por ejecución, una Policy Card que la plataforma aplica —agnóstica al modelo y autoalojada, así tu cliente nunca queda atado a un proveedor y sus siniestros nunca salen de su frontera. Cambia "siniestro de seguros" por preautorización, KYC o adjudicación de préstamos y el esqueleto no cambia. Esa portabilidad es el negocio: apréndela una vez aquí, llévala a cada cliente regulado.

**Aprenderás:** cómo declarar un pipeline en el manifiesto, cómo mantener cada etapa probable de forma independiente, cómo se hace cumplir el traspaso tipado entre etapas antes de que algo se ejecute, y el recordatorio de que **no todo paso en un pipeline de IA es un paso de IA** (la etapa de riesgo no llama a ningún modelo).

**Tiempo:** unos treinta minutos.

## Requisitos previos

- Python 3.11+
- Has hecho el [Nivel 1](../01a-doc-to-json) y el [Nivel 2](../02-grounded-reco). Este pack reutiliza ambos patrones: la etapa 1 es la extracción de doc-to-json, la etapa 3 es el gobernar-luego-explicar de grounded-reco.
- La [CLI de Huitzo](https://github.com/Huitzo-Inc/huitzo-launcher) (opcional aquí, se usa para ejecutar el pipeline contra un Hub real)

## Ejecútalo

```bash
cd pack
pip install -e ".[dev]"
pytest                  # pruebas sin conexión de este pack (lo que corre CI)
```

Deberías ver diecinueve pruebas en verde. Se ejecutan sin red y sin modelo. La mayoría verifican las tres etapas por separado; un archivo, `test_pipeline_contract.py`, carga el `huitzo.yaml` real y prueba que el pipeline está bien cableado. Esa es la prueba que más importa, y se explica más abajo.

## Qué hay dentro

```
pack/
  huitzo.yaml                          el manifiesto, incluido el bloque pipelines:
  pyproject.toml                       dependencias y los tres puntos de entrada de comando
  src/claims_pipeline/
    commands/extract_claim.py          etapa 1: lee el siniestro, prueba campos, clasifica
    commands/assess_risk.py            etapa 2: puntúa el riesgo en Python puro, sin modelo
    commands/recommend_action.py       etapa 3: decide, justifica, evalúa, audita
    risk.py                            el modelo de riesgo determinista (aparte, auditable)
    evals.py                           la decisión + la evaluación de anclaje (aparte, auditable)
    models/args.py                     entrada tipada, un modelo por etapa (el lado que consume)
    models/output.py                   salida tipada, un modelo por etapa (el lado que produce)
  tests/
    test_extract_claim.py              pruebas sin conexión de la etapa 1
    test_assess_risk.py                pruebas de la etapa 2 (afirma que el modelo nunca se llama)
    test_recommend_action.py           pruebas sin conexión de la etapa 3
    test_pipeline_contract.py          carga el manifiesto y prueba que el traspaso es sólido
```

## Un flujo de trabajo es dato, no pegamento

Abre `pack/huitzo.yaml` y busca el bloque `pipelines:`:

```yaml
pipelines:
  score-claim:
    description: "Extract a claim, assess its risk, and recommend an action, type-checked at every handoff."
    timeout: 120
    error_strategy: fail_fast
    stages:
      - name: extract
        command: "claims-pipeline:extract-claim"
      - name: assess
        command: "claims-pipeline:assess-risk"
      - name: recommend
        command: "claims-pipeline:recommend-action"
```

Ese es todo el pipeline. No hay código de orquestación: la plataforma lee este bloque, ejecuta los tres comandos en orden y alimenta la salida de cada uno a la entrada del siguiente. `error_strategy: fail_fast` significa que una etapa fallida detiene la ejecución e informa qué etapa falló, en lugar de pasar datos malos aguas abajo. Como las etapas son solo comandos, las mismas tres funciones que pruebas más abajo corren sin cambios dentro del pipeline.

## Tres comandos, con tipos verificados en cada traspaso

Cada etapa tiene una entrada tipada y una salida tipada. El contrato es simple y estricto: **cada campo que una etapa consume debe producirlo la etapa anterior.** La entrada de la etapa 2 (`AssessArgs`) es un subconjunto de la salida de la etapa 1 (`ExtractedClaim`); la entrada de la etapa 3 (`RecommendArgs`) es un subconjunto de la salida de la etapa 2 (`RiskAssessment`).

`test_pipeline_contract.py` comprueba esto sin conexión, sin ejecutor — compatibilidad de nombres de campo, un proxy rápido de la validación tipada completa que el ejecutor del Hub aplica en cada traspaso en tiempo de ejecución:

```python
handoffs = [
    (ExtractedClaim, AssessArgs),     # stage 1 output -> stage 2 input
    (RiskAssessment, RecommendArgs),  # stage 2 output -> stage 3 input
]
for producer, consumer in handoffs:
    missing = set(consumer.model_fields) - set(producer.model_fields)
    assert not missing
```

También carga el manifiesto real con el SDK y verifica que cada etapa nombre un comando que existe en el pack, en el orden que el código espera. Renombra un campo en una etapa y olvida la siguiente, y CI se pone en rojo antes de que el pipeline se ejecute de verdad. Esa es la recompensa de la composición tipada: el cableado se verifica, no se espera que funcione.

## No todo paso es un paso de IA

La etapa 2, `assess-risk`, no llama a ningún modelo. La banda de riesgo que impulsa toda la recomendación es un hecho sobre reglas fijas y documentadas (peso del tipo de siniestro, monto en dólares, una penalización por datos faltantes), así que se calcula en Python plano en `risk.py`. Un lector puede predecir la banda de cualquier siniestro a mano. Su prueba lo afirma directamente:

```python
async def test_no_model_is_ever_called(mock_ctx):
    await assess_risk(_args(), mock_ctx)
    mock_ctx.llm.complete.assert_not_called()
```

Vale la pena interiorizarlo: un pipeline no es "una cadena de llamadas al modelo". Es una cadena de pasos tipados, y la mayoría son Python determinista. El modelo aparece solo donde el juicio de verdad ayuda.

## El final gobernado

La etapa 3, `recommend-action`, es el patrón de gobernanza del Nivel 2 dentro de un pipeline. Python decide la acción a partir de la banda de riesgo; el modelo escribe una justificación de una frase para la decisión que se le entregó; una evaluación determinista comprueba que la justificación de verdad menciona el siniestro antes de confiar en ella; y se escribe un registro de auditoría detallado en cada ejecución. Una justificación sin anclaje, o una acción de escalado, se enruta a una persona. La decisión y la auditoría son de Python; el modelo se limita a una prosa que no puede usar para anular nada.

## Qué sigue (más allá de este peldaño)

Este pipeline es lineal y síncrono, que es el lugar correcto para empezar. La plataforma también admite, y puedes usar cuando esto te quede claro:

- **Etapas en streaming** que emiten resultados de forma incremental (`@command(streaming=True)`, `ctx.pipe`) para que una interfaz renderice mientras el pipeline corre.
- **Enrutamiento** (`route=` en un fragmento, `accept_routes:` en una etapa) para ramificar los siniestros de alto valor por otro camino sin `if/else`.
- **Bloques paralelos** y **etapas entre packs** que llaman a comandos de otros packs, cada llamada auditada.

Esos no se construyen aquí a propósito. Un peldaño, una idea: primero la composición declarativa y con tipos verificados.

## Ejecútalo de verdad

> Reasígnalo primero: el ejemplo usa la org `@reef`, que no es tuya. Cambia `namespace:` en `huitzo.yaml` por una org que poseas y ejecuta `huitzo pack sync` antes de publicar. Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub).

Cada etapa es un comando normal, así que puedes ejecutarlas de una en una:

```bash
huitzo login
huitzo run @your-org/claims-pipeline/assess-risk --args '{"claim_id": "C-1", "claim_type": "liability", "claim_amount": 300000, "requires_review": false, "missing_fields": []}'
```

Cuando tengas acceso anticipado a un Hub, ejecuta todo el pipeline por la API REST:

```bash
curl -X POST https://huitzo.ai/api/v1/pipelines/reef/claims-pipeline/score-claim/execute \
  -H "Authorization: Bearer sk-huitzo-..." \
  -H "Content-Type: application/json" \
  -d '{"initial_args": {"claim_id": "C-1", "document_text": "Policy number HMO-4471829. Incident date 2026-05-12. Damage of $12,500.00."}}'
```

## Siguiente

Has compuesto packs en el backend. El [Nivel 4: first-dashboard](../04-first-dashboard) le pone cara a uno: una app de React que llama a un pack desde el navegador, sin backend propio.
