<!-- i18n-source-sha: 747cd42bc8f4a426aacf9b4fdb3279cc08f4e1889a6254a77857fc709ffda377 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 0: hello-pack

> Read this in [English](./README.md).

El Intelligence Pack completo más pequeño. Entra texto, una llamada al modelo pasa por el SDK y regresa un resultado tipado y validado. Si haces una sola cosa en este repo, haz esta. Es la ruta más rápida a un pack funcionando y siembra la idea sobre la que se construye todo lo demás: **el código Python determinista se encarga de lo que puede, y al modelo se le pide solo la parte que Python no puede hacer.**

**Aprenderás:** el decorador `@command`, argumentos y salida tipados con Pydantic, cómo llamar a un modelo a través de un perfil (nunca un nombre de modelo fijo) y cómo probar un pack sin conexión.

**Tiempo:** unos cinco minutos.

## Requisitos previos

- Python 3.11+
- La [CLI de Huitzo](https://github.com/Huitzo-Inc/huitzo-launcher) (opcional en este peldaño, se usa para ejecutar contra un Hub real)

## Ejecútalo

```bash
cd pack
pip install -e ".[dev]"
pytest                  # pruebas sin conexión de este pack (lo que corre CI)
```

Deberías ver tres pruebas en verde. Se ejecutan sin red y sin modelo: la prueba le entrega al comando un contexto falso cuya llamada al modelo está simulada, así tu lógica se verifica sin gastar un token.

## Constrúyelo tú mismo (la forma más rápida de aprender)

Leer código que funciona es más lento que escribirlo. Prueba esto primero:

1. Abre `src/hello_pack/commands/hello.py` y borra el cuerpo de `hello`, dejando
   solo `async def hello(args: HelloArgs, ctx: Context) -> TextInsight:` y un
   `raise NotImplementedError`.
2. Ejecuta `pytest`. Falla — **las pruebas son la especificación.**
   Léelas en `tests/test_hello.py`: te dicen exactamente qué debe hacer el comando
   (calcular el conteo de palabras en Python, llamar al modelo para el juicio,
   devolver un `TextInsight` tipado).
3. Vuelve a implementar los tres pasos hasta que las pruebas pasen. El bloque bajo
   ["El comando, línea por línea"](#el-comando-línea-por-línea) es la solución si
   te atascas.

Ese bucle —una prueba que falla y fija el contrato, luego código hasta el verde—
es cómo construirás cada pack real. El resto de este README explica la solución.

## Qué hay dentro

```
pack/
  huitzo.yaml                  el manifiesto: identidad, permisos, la Policy Card
  pyproject.toml               dependencias y el punto de entrada del comando
  src/hello_pack/
    commands/hello.py          el comando en sí
    models/args.py             entrada tipada (validada antes de que corra tu código)
    models/output.py           salida tipada (lo que devuelve el modelo + un dato de Python)
  tests/test_hello.py          pruebas sin conexión
```

## El comando, línea por línea

```python
@command("hello", namespace="reef", timeout=30)
async def hello(args: HelloArgs, ctx: Context) -> TextInsight:
    # 1) Primero lo determinista. Python se encarga de lo que puede hacer de forma fiable.
    word_count = len(args.text.split())

    # 2) Aumento con IA. Una llamada, a un *perfil*, que devuelve un modelo validado.
    insight = await ctx.llm.complete(
        prompt=f"{_PROMPT}\n\n<text>\n{args.text}\n</text>",
        profile="default",
        schema=ModelInsight,
    )

    # 3) Combina el juicio del modelo con el dato determinista.
    return TextInsight(word_count=word_count, **insight.model_dump())
```

Tres cosas para notar:

1. **El conteo de palabras se calcula en Python, no se le pide al modelo.** Todo lo determinista sigue siendo determinista. El modelo nunca es el cuello de botella ni la fuente de errores evitables.
2. **`profile="default"` no es un nombre de modelo.** El pack declara un perfil de capacidad; el despliegue lo asigna a un proveedor y modelo concretos. Así cambias OpenAI por Anthropic, o un modelo en la nube por uno local, sin tocar este archivo.
3. **`schema=ModelInsight` devuelve una instancia validada,** no una cadena que tengas que parsear. La salida estructurada es el traspaso por defecto entre tu código y el modelo.

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
huitzo run @your-org/hello-pack/hello --args '{"text": "Huitzo hace que la IA funcione donde viven tus datos."}'
```

## Siguiente

Nivel 1: [`doc-to-json`](../) lee un documento real desde el almacenamiento y devuelve campos tipados. El mismo patrón, más superficie.
