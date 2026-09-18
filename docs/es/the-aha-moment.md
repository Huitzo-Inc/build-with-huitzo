<!-- i18n-source-sha: 7153f8485ef1458810174eb7bc006fcd2117a3813a7e0dedaad07596d9593e1d -->
# El momento "ajá": cambia el modelo, conserva la gobernanza

Esto es lo único que necesitas sentir antes de construir algo serio sobre Huitzo.

Un Intelligence Pack de Huitzo nunca nombra un modelo. Pide un **perfil** —una
etiqueta de capacidad— y es el *despliegue* quien decide a qué modelo concreto se
resuelve. Así puedes mover un pack de Claude a GPT‑4o a un modelo local
**cambiando una sola línea de configuración del despliegue**, con **cero cambios
en tu código** y **cero cambios en la decisión gobernada o en el registro de
auditoría**.

Este recorrido lo demuestra sobre un pack gobernado real, con salida real.

> **No nos creas — ejecútalo sin conexión en cinco segundos (sin Hub, sin API key):**
> ```bash
> cd projects/02-grounded-reco/pack && pip install -e ".[dev]"
> python -m grounded_reco.demo_model_swap
> ```
> Ejecuta el comando `recommend` *real* bajo dos "modelos" simulados distintos y los
> imprime lado a lado: la elección, la compuerta de evaluación y la auditoría salen
> **idénticas al byte** (Python determinista que el modelo nunca toca); solo cambia la
> prosa de la justificación. Ese es todo el argumento, mostrado en vez de afirmado.

## El pack que usaremos: [`02-grounded-reco`](../../projects/02-grounded-reco)

`recommend` es una recomendación gobernada. El orden de las operaciones *es* la
historia de la gobernanza:

1. **Python** puntúa y ordena las candidatas y elige la opción. El modelo no
   elige.
2. El **modelo** escribe una justificación de una frase para la opción *elegida
   por Python*. Recibe la decisión y los números, y se le indica que no los
   cambie.
3. Una **evaluación determinista** (frescura + fundamentación) juzga el resultado
   *antes* de que llegue a un usuario. Si falla, la recomendación se retiene y se
   escala.
4. Se produce y registra un **registro de auditoría** detallado en cada ejecución.

La llamada al modelo es exactamente esta —fíjate en el `profile`, nunca un nombre
de modelo:

```python
justification: Justification = await ctx.llm.complete(
    prompt=prompt,
    profile="default",     # una etiqueta de capacidad — NO "claude" ni "gpt-4o"
    schema=Justification,  # salida tipada y validada (ver "el momento ajá", parte 2)
)
```

## Ejecución 1 — sobre Claude (el modelo por defecto del despliegue)

```bash
huitzo run @reef/grounded-reco/recommend --args '{
  "objective": "Choose the vendor that best balances reliability and cost for a regulated healthcare client.",
  "freshness_days": 3650,
  "candidates": [
    {"name": "NorthAPI",     "cost": 0.30, "quality": 0.80, "reliability": 0.95, "as_of": "2026-06-10"},
    {"name": "BudgetStream", "cost": 0.10, "quality": 0.55, "reliability": 0.60, "as_of": "2026-06-12"},
    {"name": "PremiumCloud", "cost": 0.85, "quality": 0.92, "reliability": 0.90, "as_of": "2026-06-01"}
  ]
}'
```

Salida real de un Hub en vivo ejecutando `claude-sonnet-4-6`:

```json
{
  "pick": "NorthAPI",
  "score": 0.815,
  "ranked": [
    {"name": "NorthAPI",     "score": 0.815, "as_of": "2026-06-10"},
    {"name": "PremiumCloud", "score": 0.683, "as_of": "2026-06-01"},
    {"name": "BudgetStream", "score": 0.670, "as_of": "2026-06-12"}
  ],
  "justification": "NorthAPI earned the top score of 0.815, meaningfully ahead of PremiumCloud (0.683) and BudgetStream (0.670), indicating it best balances reliability and cost for a regulated healthcare client according to the deterministic scoring system.",
  "eval_passed": true,
  "eval_findings": [
    "freshness: OK, pick 'NorthAPI' within 3650 days.",
    "grounding: OK, justification references the pick."
  ],
  "withheld": false,
  "escalated": false,
  "audit": {
    "timestamp": "2026-06-18T18:20:27Z",
    "autonomy": "suggest",
    "candidate_count": 3,
    "pick": "NorthAPI",
    "eval_passed": true,
    "eval_findings": ["freshness: OK, pick 'NorthAPI' within 3650 days.",
                      "grounding: OK, justification references the pick."],
    "escalated": false
  }
}
```

## Ejecución 2 — cambia a GPT‑4o modificando UNA línea

En la configuración del despliegue (la del operador del Hub, no la tuya), cambia
un valor y reinicia:

```diff
  HUITZO_LLM_CLOUD_ENABLED: "true"
  HUITZO_LLM_ROUTING_MODELS: '[{"name":"claude-sonnet-4-6",...},{"name":"gpt-4o",...}]'
- HUITZO_LLM_ROUTING_DEFAULT_MODEL: claude-sonnet-4-6
+ HUITZO_LLM_ROUTING_DEFAULT_MODEL: gpt-4o
```

Vuelve a ejecutar **exactamente el mismo comando**. Lo verificamos en vivo: el
pack idéntico, sin cambios, enrutó su llamada al modelo al endpoint `gpt-4o` de
OpenAI en lugar de Anthropic, y produjo el **resultado determinista idéntico al
byte** antes de consultar siquiera al modelo:

```
recommend: deterministic pick='NorthAPI' score=0.815 from 3 candidates
HTTP Request: POST https://api.openai.com/v1/chat/completions   ← ahora GPT-4o, no Anthropic
```

## Qué cambió, y qué no

| | Ejecución 1 (Claude) | Ejecución 2 (GPT‑4o) |
|---|---|---|
| **La decisión** — opción, puntuación, orden | `NorthAPI`, `0.815` | `NorthAPI`, `0.815` — *idéntica* |
| **La barrera** — eval de frescura + fundamentación, retener/escalar | aprobada, no retenida | *idéntica* |
| **El registro de auditoría** — autonomía, hallazgos, escalado | registrado | *idéntico* |
| **La Policy Card** — `autonomy: suggest`, rutas de escalado | aplicada | *idéntica* |
| La prosa de **justificación** de una frase | redacción de Claude | redacción de GPT‑4o |

Solo cambió el *autor de la prosa*. Todo lo que gobierna la decisión es Python
determinista, así que es **independiente del modelo por construcción** —cambiar
el modelo *no puede* cambiar una decisión, porque el modelo nunca tomó ninguna.
El modelo se limita a una justificación que la evaluación luego verifica por su
fundamentación.

## El detalle clave (algo que ocurrió de verdad)

Cuando ejecutamos el cambio en vivo, la clave de OpenAI del despliegue
estaba limitada por tasa (HTTP 429). El despliegue no se rompió y no cambió
ningún código: volvimos a poner la única línea en `claude-sonnet-4-6` y volvió a
responder en segundos.

**Ese es justamente el punto.** La cuota de un proveedor, una caída, un cambio de
precio o la baja de un modelo es un *cambio de configuración de operaciones* para
un despliegue de Huitzo —no una reescritura de código y un redespliegue. La
solución de tu cliente nunca queda atada a un solo proveedor.

## ¿Por qué no usar simplemente el SDK de Anthropic + Pydantic?

Por supuesto que puedes llamar a un modelo y validar el JSON tú mismo. Esto es lo
que asumes el día que lo haces, y lo que Huitzo te da en su lugar:

| Lo que quieres… | SDK de Anthropic + Pydantic | Intelligence Pack de Huitzo |
|---|---|---|
| **Cambiar el modelo / proveedor** | Reescribir el cliente, volver a probar, redesplegar. Tu cliente queda atado a tu único proveedor. | Una línea de configuración del despliegue. Cero cambios de código. Sin atadura de proveedor para *tus* clientes. |
| **Salida estructurada fiable** | Programar a mano un bucle de reintento que devuelve los errores de validación al modelo. | Incluido — `schema=` valida y se autocorrige ante un fallo de validación. |
| **Una barrera antes de que la salida llegue a un usuario** | Construir y mantener tu propia lógica de eval/retención/escalado. | **Policy Card** declarativa + evals deterministas que el framework ejecuta siempre. |
| **Un registro de auditoría por cada generación** | Construirlo, almacenarlo, demostrarlo ante un auditor. | Cada ejecución es auditada por el framework, devuelta y registrada. |
| **Autoalojado, sin acceso para datos regulados** | Construir y certificar la infraestructura tú mismo. | Se ejecuta dentro de tu tenant; el modelo se llama donde ya viven tus datos. |

El modelo es la parte fácil. **La gobernanza, la auditabilidad y no quedar
rehén de un solo proveedor son las partes difíciles —y son exactamente lo que un
Pack te da gratis.** Por eso un partner construye la solución regulada de un
cliente sobre Huitzo en lugar de cablear el SDK directamente.

## Pruébalo tú mismo

1. Ejecuta [`02-grounded-reco`](../../projects/02-grounded-reco) contra tu propio
   Hub (ver [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub)).
2. Pide a tu operador del Hub que alterne `HUITZO_LLM_ROUTING_DEFAULT_MODEL` entre
   dos modelos que tu despliegue tenga configurados, y que reinicie.
3. Vuelve a ejecutar el mismo comando. Observa cómo la decisión, la evaluación y
   la auditoría permanecen idénticas mientras solo cambia la prosa.

Siguiente: [`03-claims-pipeline`](../../projects/03-claims-pipeline) muestra la
misma gobernanza escalada a un entregable multietapa para una industria regulada.
