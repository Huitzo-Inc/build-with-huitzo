<!-- i18n-source-sha: 75f8f8bcb98ed0ad14074c577bd8c3e322c48f4bf4b92d190083be60f21460f8 -->
# Solución de referencia: trade-surveillance (mercados financieros)

> Read this in [English](./README.md).

Esta es la primera de las **soluciones de referencia reguladas** — no un peldaño de enseñanza, sino un punto de partida creíble que un partner adapta para un cliente real. Aplica el mismo patrón gobernado que aprendiste en la escalera ([Nivel 2](../02-grounded-reco), [Nivel 3](../03-claims-pipeline)) a la **vigilancia de abuso de mercado** para un broker-dealer o una gestora de activos.

Llega una operación. Código Python determinista ejecuta detectores fijos y documentados para los patrones clásicos de abuso —precio fuera de mercado, marcar el cierre, layering/spoofing, operaciones de lavado, anomalías de tamaño— y calcula una puntuación y una banda de riesgo. **Solo cuando algo se activa** el modelo escribe una nota de alerta breve para un analista de cumplimiento. Una evaluación determinista comprueba que esa nota esté fundamentada antes de que alguien la vea, y Python —nunca el modelo— decide si la alerta se descarta, va a revisión o se escala a una persona. Cada análisis deja un registro de auditoría detallado.

> **Léelo como un entregable real.** La vigilancia es una de las superficies de IA más reguladas de los mercados de capitales (MAR, FINRA, SEC). Lo que la hace defendible es exactamente la forma de Huitzo: la *detección y la decisión son deterministas, reproducibles y auditables*, y el modelo se limita a una prosa que una barrera verifica. Cambia los detectores por monitoreo de transacciones AML, revisión de idoneidad/mejor ejecución, o controles de divulgación, y el esqueleto no cambia. Esa portabilidad es el producto del partner: adáptalo por cliente y revéndelo autoalojado para que el flujo de órdenes del cliente nunca salga de su frontera.

**Aprenderás / qué demuestra:** el patrón gobernado escala directo de un juguete a un entregable regulado de mercados de capitales; la detección determinista decide si se activa una alerta (el modelo no puede levantar ni suprimir una); una evaluación de fundamento y una compuerta de escalado humano se sitúan entre el modelo y el analista; y cada análisis queda auditado — agnóstico al modelo y autoalojado de principio a fin.

## Ejecútalo

```bash
cd pack
pip install -e ".[dev]"
pytest                  # pruebas sin conexión de este pack (lo que corre CI)
```

Deberías ver diez pruebas en verde, sin red y sin modelo. Codifican el contrato de gobernanza: una operación limpia se descarta sin llamar nunca al modelo; una operación marcada se narra, se evalúa y se escala; y —la prueba clave— el **modelo no puede cambiar la disposición** (una alerta de alto riesgo se escala aunque la narrativa diga "se ve bien").

## El flujo gobernado

```python
# 1) DETECCIÓN DETERMINISTA — Python decide si se activa una alerta y cuán severa es.
signals = rules.detect_signals(trade, market)
risk_score = rules.score(signals)
risk_band = rules.band(risk_score)

# 2) Una operación limpia nunca llama al modelo. Determinista para el 99% tranquilo.
if not signals:
    return SurveillanceAlert(..., disposition="clear", ...)

# 3) NARRACIÓN CON IA — una llamada, a un perfil, que devuelve una instancia validada. El
#    modelo explica la alerta que Python levantó; no puntúa, ni clasifica, ni dispone.
narrative = await ctx.llm.complete(prompt=..., profile="default", schema=AlertNarrative)

# 4) EVAL + DISPOSICIÓN + AUDITORÍA — todo Python determinista.
eval_passed, findings = evals.run_eval(trade.symbol, signals, narrative.text)
disposition = evals.decide_disposition(risk_band, eval_passed)   # clear | review | escalate
```

## Los detectores son el núcleo auditable

`rules.py` contiene todo el modelo de detección en Python legible —umbrales y pesos fijos que un oficial de cumplimiento puede leer, defender y ajustar, sin ningún modelo cerca del veredicto:

| Señal | Se activa cuando | Peso |
|---|---|---|
| `off_market_price` | la ejecución está > 2% del mid prevaleciente | 0.35 |
| `marking_the_close` | print agresivo en los últimos 5 minutos | 0.30 |
| `layering_spoofing` | ratio de cancelación reciente ≥ 80% | 0.30 |
| `wash_trade` | mismo titular beneficiario en ambos lados | 0.40 |
| `size_anomaly` | ≥ 10× el tamaño promedio del trader | 0.20 |

La puntuación compuesta es una suma ponderada con tope; los umbrales de banda son constantes. Puedes predecir la banda de cualquier operación a mano — ese es el punto: un regulador también puede.

## Por qué esto no es una envoltura delgada sobre un LLM

Una envoltura le preguntaría al modelo "¿esto es sospechoso?" y devolvería la respuesta. Esto hace lo contrario, y esa inversión es lo que lo hace desplegable en una firma regulada:

1. **La detección es determinista.** El modelo nunca decide si se activa una alerta; `rules.py` lo hace, de forma reproducible.
2. **El modelo solo narra, y la narrativa se revisa.** Una nota sin fundamento (que no nombra ni el instrumento ni un patrón activado) nunca se confía — se escala a una persona.
3. **La disposición es de Python.** `decide_disposition` enruta a partir de la banda + la evaluación; el modelo no puede descartar una alerta de alto riesgo. Una prueba lo afirma.
4. **Cada análisis queda auditado.** Una operación descartada deja la misma evidencia que una escalada, así nada es invisible para un examinador. La Policy Card (`autonomy: suggest`, `escalation`, `audit: detailed`) es el contrato que la plataforma hace cumplir.

## Adáptalo para un cliente

Está hecho para reorientarse. Para convertirlo en otra vigilancia de mercados o en otra vertical:

- Edita `rules.py`: cambia los detectores, umbrales y pesos al apetito de riesgo y al reglamento del cliente (p. ej. reglas de monitoreo de transacciones AML, controles de idoneidad).
- Conserva la forma: detección → (el modelo narra) → evaluación → disposición determinista → auditoría.
- Reasigna el namespace a una org que poseas (`huitzo.yaml` → `huitzo pack sync`) y publica en el Hub autoalojado del cliente. Su flujo de órdenes nunca sale de su frontera.

## Ejecútalo de verdad

> Reasígnalo primero: el ejemplo usa la org `@reef`. Cambia `namespace:` en `huitzo.yaml` por una org que poseas y ejecuta `huitzo pack sync` antes de publicar. Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub).

```bash
huitzo login
huitzo run @your-org/trade-surveillance/screen-trade --args '{
  "trade":  {"trade_id": "T-9", "symbol": "ACME", "side": "buy", "quantity": 100, "price": 103.10, "timestamp": "2026-06-19T15:58:30Z"},
  "market": {"prevailing_bid": 100.00, "prevailing_ask": 100.10, "minutes_to_close": 2, "trader_avg_quantity": 100, "recent_cancel_ratio": 0.0}
}'
```
