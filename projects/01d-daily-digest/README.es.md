<!-- i18n-source-sha: 3ca2727ba9f42fa3aeeb5d16a01d144abd366496d4617d659f6d406a1541db85 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 1: daily-digest

> Read this in [English](./README.md).

Un día de trabajo real en un solo pack. Tide Mart, una tienda de conveniencia de una sola sucursal, suelta un CSV de ventas diarias. Este pack lo convierte en un resumen en lenguaje claro más una sola alerta de anomalía: qué día se salió del patrón, por cuánto y cómo se vio el día en general. Es el peldaño al alcance del indie hacker. Las mismas primitivas sirven a un dueño de una sucursal y a un conglomerado; lo único que cambia es el tamaño del CSV.

La idea que hay que llevarse de aquí: **Python encuentra la anomalía; el modelo solo la narra.** Cada número y cada alerta se calcula de forma determinista en Python puro. Al modelo se le pide una sola cosa, la prosa amable, y se le entregan las cifras para que no pueda inventarlas.

**Aprenderás:** diseño determinista primero con el módulo `csv` de la biblioteca estándar, detección de anomalías en Python puro (z-score con un respaldo por porcentaje), cómo anclar una llamada al modelo en cifras que ya calculaste y cómo probar todo esto sin conexión.

**Tiempo:** unos diez minutos.

## Requisitos previos

- Python 3.11+
- La [CLI de Huitzo](https://github.com/Huitzo-Inc/huitzo-launcher) (opcional en este peldaño, se usa para ejecutar contra un Hub real)

## Ejecútalo

```bash
cd pack
pip install -e ".[dev]"
pytest                  # pruebas sin conexión de este pack (lo que corre CI)
```

Deberías ver cuatro pruebas en verde. Se ejecutan sin red y sin modelo: las pruebas le entregan al comando un contexto falso cuya llamada al modelo está simulada, así los totales y las alertas de anomalía se verifican sin gastar un token.

## Qué hay dentro

```
pack/
  huitzo.yaml                       el manifiesto: identidad, permisos, la Policy Card
  pyproject.toml                    dependencias y el punto de entrada del comando
  src/daily_digest/
    commands/daily_digest.py        parsea, suma, marca anomalías y luego una llamada al modelo
    models/args.py                  entrada tipada (el CSV crudo, validado antes de que corra tu código)
    models/output.py                salida tipada (cada cifra de Python + la prosa del modelo)
  tests/test_daily_digest.py        pruebas sin conexión
```

## El comando, en tres movimientos

```python
@command("daily-digest", namespace="reef", timeout=30)
async def daily_digest(args: DigestArgs, ctx: Context) -> DailyDigest:
    # 1) Primero lo determinista. Python parsea el CSV y se encarga de cada número.
    #    Totales, totales por categoría, categoría principal, conteo de días, filas omitidas.

    # 2) Detección de anomalías, en Python puro. Compara cada día con la media de los
    #    demás: un z-score cuando hay suficientes días, una regla por porcentaje cuando no.
    anomalies = _detect_anomalies(daily_totals)

    # 3) Aumento con IA. Una llamada, a un *perfil*, con las cifras calculadas entregadas
    #    para que la prosa quede anclada. El modelo llena exactamente un campo: el resumen.
    narrative = await ctx.llm.complete(
        prompt=f"{_PROMPT}\n\n<data>\n{facts}\n</data>",
        profile="default",
        schema=DigestNarrative,
    )
    return DailyDigest(..., anomalies=anomalies, summary=narrative.summary)
```

Tres cosas para notar:

1. **La anomalía se encuentra en Python, no se le pide al modelo.** Un día con un pico es un hecho sobre números. Python calcula la media y la dispersión de los demás días y marca el valor atípico, así la alerta es reproducible y auditable. Un modelo podría pasarla por alto o alucinar una; la regla determinista no hace ninguna de las dos.
2. **`profile="default"` no es un nombre de modelo.** El pack declara un perfil de capacidad; el despliegue lo asigna a un proveedor y modelo concretos. Así cambias OpenAI por Anthropic, o un modelo en la nube por uno local, sin tocar este archivo.
3. **El modelo está anclado, no se le confía la aritmética.** El total calculado, la categoría principal y los días marcados se formatean en el prompt, y se le indica al modelo que use solo esas cifras. Escribe la frase; nunca decide el número.

## Por qué importa aquí lo determinista primero

Un dueño que lee este resumen está tomando una decisión: averiguar por qué el sábado tuvo un pico, o confiar en que la semana fue estable. Si el número que impulsa esa decisión viniera de un modelo que podría equivocarse en un dígito, el resumen es peor que inútil. Por eso el número nunca viene del modelo. Python lo calcula; el modelo solo lo pone en una frase amable. Esa división es todo el patrón de Huitzo, y es justo lo que permite que el mismo pack sea de confianza para una tienda de barrio y para un equipo de finanzas que opera mil sucursales.

## El momento "cambia el modelo"

Abre `pack/huitzo.yaml` y busca el bloque `services.llm`:

```yaml
services:
  llm:
    required: true
    requirements:
      min_context: 8000
      capabilities:
        - structured_output
```

El pack declara lo que necesita (una ventana de contexto y salida estructurada), no qué modelo lo provee. En tu Hub, el perfil `default` se resuelve al modelo para el que esté configurado ese despliegue. El mismo pack corre sin cambios en un modelo local o en la nube. Esa es la promesa de agnosticismo de modelo, hecha concreta.

## Ejecútalo de verdad

> Reasígnalo primero: el ejemplo usa la org `@reef`, que no es tuya. Cambia `namespace:` en `huitzo.yaml` por una org que poseas y ejecuta `huitzo pack sync` antes de publicar. Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub).

Cuando tengas acceso anticipado a un Hub:

```bash
huitzo login
huitzo run @your-org/daily-digest/daily-digest --args '{"sales_csv": "date,category,amount\n2026-06-01,snacks,120\n2026-06-01,drinks,80"}'
```

## Siguiente

El mismo patrón, más superficie. La forma nunca cambia: Python se encarga de los hechos, el modelo escribe la prosa. El peldaño gobernado, [02-grounded-reco](../02-grounded-reco), añade una evaluación y un rastro de auditoría sobre este núcleo.
