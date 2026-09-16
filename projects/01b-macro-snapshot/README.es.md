<!-- i18n-source-sha: d71c92543bbf257aac86cf188191f70a4901190a36432980b660c05d18b22446 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 1: macro-snapshot

> Read this in [English](./README.md).

Un pack que llega a una API real. Una mesa de investigación ficticia, **Marlin Research**, quiere una lectura bien fundamentada de la economía de un país: traer un indicador macro del Banco Mundial y recibir de vuelta un resumen en lenguaje claro. El detalle, y aquí está todo el sentido: **el modelo nunca produce un número.** Python trae los datos, elige la observación más reciente y calcula el cambio. Al modelo se le entregan esas cifras y se le pide solo que escriba la frase. Esto es lo que significa "IA fundamentada" en la práctica. Los números son hechos; el modelo los narra.

**Aprenderás:** cómo llamar a una API externa a través de `ctx.http` (el host lo configura el despliegue, no se fija en el código), el parseo defensivo de una respuesta real, la división determinista-primero hecha en serio, y cómo evitar que un modelo invente cifras dándole solo las cifras que tiene permitido usar.

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

Deberías ver ocho pruebas en verde. Se ejecutan sin red y sin modelo: la prueba le entrega al comando un contexto falso cuyas llamadas HTTP y al modelo están ambas simuladas, así tu parseo y tu aritmética se verifican sin una API real ni un token gastado.

## Qué hay dentro

```
pack/
  huitzo.yaml                          el manifiesto: identidad, permisos, la Policy Card
  pyproject.toml                       dependencias y el punto de entrada del comando
  src/macro_snapshot/
    commands/country_snapshot.py       el comando en sí
    models/args.py                     entrada tipada (conjuntos cerrados de país e indicador)
    models/output.py                   salida tipada (los números de Python + la frase del modelo)
  tests/test_country_snapshot.py       pruebas sin conexión
```

## El comando, la forma que importa

```python
@command("country-snapshot", namespace="reef", timeout=30)
async def country_snapshot(args: SnapshotArgs, ctx: Context) -> CountrySnapshot:
    code = _INDICATOR_CODES[args.indicator]            # nombre amigable -> código WB, en Python

    raw = await ctx.http.get(                           # el host es la integración, la ruta es relativa
        f"/v2/country/{args.country}/indicator/{code}",
        params={"format": "json", "mrv": 5},
    )
    data = json.loads(raw) if isinstance(raw, str) else raw   # dict o cadena JSON, ambos manejados

    # Primero lo determinista: Python elige el punto más reciente no nulo y el delta.
    latest_value, latest_year, delta_pct = _latest_and_delta(data[1])

    # Aumento con IA: entrega al modelo solo las cifras parseadas, pide una frase.
    narration = await ctx.llm.complete(
        prompt=f"{_PROMPT}\n\n<figures>\n{facts}\n</figures>",
        profile="default",
        schema=MacroSummary,
    )

    return CountrySnapshot(latest_value=latest_value, ..., summary=narration.summary)
```

Cuatro cosas para notar:

1. **Los números vienen de Python, la frase viene del modelo.** `latest_value`, `latest_year` y `delta_pct` se calculan a partir de la respuesta del Banco Mundial. El modelo recibe esas cifras y escribe el resumen. Nunca se le pide hacer aritmética ni recordar una estadística, así que no puede equivocarse en una.
2. **El modelo solo ve las cifras que tiene permitido repetir.** El prompt contiene exactamente los números parseados, con la instrucción de usar solo esos y no inventar nada. Esa es la diferencia entre un modelo que narra tus datos y uno que se inventa cosas.
3. **El host es la integración, no el código.** `ctx.http.get` recibe una ruta relativa. La URL base (`api.worldbank.org`) se configura en el despliegue y se incluye en la lista de permitidos del manifiesto. Cambia esa integración por una API interna y el comando no cambia ni una línea.
4. **La respuesta se parsea de forma defensiva.** El Banco Mundial devuelve una lista de dos elementos, `[metadatos, observaciones]`, y el valor puede ser una cadena JSON o ya estar parseado. El comando maneja ambos y lanza un `ExternalAPIError` claro ante una forma inesperada, en lugar de un `KeyError` opaco en lo profundo de tu lógica.

## El momento "cambia cualquier API interna"

Abre `pack/huitzo.yaml` y busca el bloque `services.http`:

```yaml
services:
  http:
    required: true
    allowed_domains:
      - "api.worldbank.org"
    timeout: 15
```

El pack declara a qué host tiene permiso de llegar. La URL base la resuelve la integración HTTP del despliegue. Hoy es el Banco Mundial. Mañana es tu data warehouse, tu servicio de precios o tu base de datos de siniestros, con el mismo código de comando y la misma división determinista-primero. El patrón es el producto: Python se encarga de la aritmética, el modelo se encarga de la frase, y la fuente de datos es un detalle del despliegue.

Nota el cruce que impone el manifiesto: cada dominio en `services.http.allowed_domains` también debe aparecer en `policy.data_scope.external_domains`. Un pack solo puede llegar a lo que su Policy Card permite.

## Ejecútalo de verdad

Dos pasos de configuración únicos y luego puedes ejecutar este pack contra un Hub.

### 1. Reasígnalo a una org que poseas

El ejemplo está bajo `@reef`, que no es tuya. En `pack/huitzo.yaml`, cambia `namespace:` por una org que poseas, luego sincroniza y publica:

```bash
huitzo login
# pack/huitzo.yaml -> pack.namespace: tu-org   (antes: reef)
huitzo pack sync
huitzo pack publish
```

Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub) para la explicación completa.

### 2. Añade la integración del Banco Mundial en Hub

Este pack llega a `api.worldbank.org` a través de una **integración** HTTP, no de una URL fija. El comando llama a `ctx.http.get("/v2/country/...")` con una ruta relativa, y el despliegue provee la URL base. Así que añade esa integración una vez en el Hub antes de la primera ejecución real:

1. Abre el Hub y haz clic en **Integrations** en la barra lateral izquierda (la página `/integrations`).

   <!-- screenshot: the Integrations page with the "+ Add integration" button -->

2. Haz clic en **+ Add integration**. En el formulario, configura:
   - **Type**: `HTTP`
   - **Name**: `worldbank` (cualquier slug único en tu tenant; minúsculas, dígitos, guiones)
   - **Base URL**: `https://api.worldbank.org`
   - **Timeout (s)**: `30` (el valor por defecto está bien)
   - **Allowed domains (CSV)**: déjalo en blanco (el host de la URL base se permite automáticamente)
   - **Bearer token** / **Basic auth**: déjalos en blanco (la API del Banco Mundial no necesita autenticación)

   <!-- screenshot: the New integration form filled in for the World Bank API -->

3. Haz clic en **Create integration**. El Hub corre una sonda de salud contra la URL base; cuando se muestre sana, la integración está lista.

   <!-- screenshot: the created worldbank integration showing a healthy status -->

El nombre de la integración no necesita coincidir con nada del pack. En tiempo de ejecución el despliegue conecta tu integración HTTP al `ctx.http` de este pack, así que `ctx.http.get("/v2/country/USA/indicator/...")` se resuelve a `https://api.worldbank.org/v2/country/USA/indicator/...`. (¿Prefieres la API? `POST /api/v1/integrations` con `{"type":"http","name":"worldbank","config":{"base_url":"https://api.worldbank.org"}}`.)

### 3. Ejecútalo

```bash
huitzo run @tu-org/macro-snapshot/country-snapshot --args '{"country": "USA", "indicator": "gdp"}'
```

## Siguiente

[Nivel 1: `01c-inbox-triage`](../01c-inbox-triage) es el siguiente peldaño: las reglas deterministas deciden qué tan urgente es un correo, el modelo solo redacta una respuesta y el pack nunca la envía. El mismo patrón, más superficie: primero la lógica determinista, el modelo solo para el juicio, y cada acceso externo declarado en la Policy Card.

> ¿Vas a construir un dashboard? Este es el pack al que [Nivel 4: `04-first-dashboard`](../04-first-dashboard) le pone una interfaz. Puedes saltar allí ahora: no necesita nada de los Niveles 2 ni 3.
