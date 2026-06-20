<!-- i18n-source-sha: 67227b34884d7ed3634d4f829fb878712e719b2cbf71b9a59151a2fd6339fbd4 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 5: pack-from-outside

> Read this in [English](./README.md).

Hasta ahora has construido cosas que corren dentro de Huitzo: packs, un pipeline, un dashboard. Este peldaño va en sentido contrario. Reef Supply Co. tiene un pack desplegado y quiere llamarlo desde sus propios sistemas: un script de shell, un servicio de backend, un asistente de IA, un pipeline de CI. Así se maneja un pack de Huitzo desde fuera.

La idea que hay que llevarse de aquí: **hay un solo modelo mental y cuatro puertas hacia él.** REST, la CLI, el servidor MCP alojado y una acción de CI no son cuatro productos distintos. Son cuatro formas de hacer los mismos cuatro pasos:

```
  una clave (commands:execute)  ->  ejecutar un comando  ->  resultado síncrono o tarea async  ->  desenvolver {data: ...}
        REST  |  CLI  |  MCP alojado  |  acción de CI
```

**Aprenderás:** cómo autenticarte con una clave de API, cómo ejecutar un comando por REST y manejar la división síncrono-contra-asíncrono, cómo la CLI asigna desenlaces a códigos de salida, cómo el servidor MCP alojado deja que Claude o Cursor llamen a tu pack, y cómo una acción de CI condiciona un merge a la salida de un pack.

**Tiempo:** unos cuarenta minutos.

## Una nota sobre la estructura

Este peldaño es un **cliente**, no un pack. No tiene carpeta `pack/` ni `huitzo.yaml`, a propósito: estás consumiendo un pack, no escribiéndolo. Por eso el diseño de abajo se ve distinto de los demás peldaños.

## Ejecútalo

El cliente de Python incluye pruebas que corren completamente sin conexión (la capa HTTP está simulada), así que puedes verificar la lógica del cliente sin Hub y sin clave:

```bash
cd python
pip install -e ".[dev]"
pytest -q        # 7 pruebas en verde
```

Para llamar a un pack real necesitas un pack desplegado y una clave de API con el alcance `commands:execute`. Cada comando "de verdad" más abajo está condicionado a eso.

## Qué hay dentro

```
05-pack-from-outside/
  curl/run.sh            Puerta 1, cruda: la petición en el cable, con curl
  python/
    huitzo_client.py     Puerta 1, ergonómica: un cliente httpx diminuto (sync/async, reintentos)
    mcp_client.py        Puerta 3: un cliente JSON-RPC de MCP escrito a mano
    test_huitzo_client.py    pruebas sin conexión (simuladas con respx): envoltura, sondeo async, 429, errores
    test_mcp_client.py       pruebas sin conexión: mapeo de nombres de herramienta, initialize/list/call
  cli/USAGE.md           Puerta 2: huitzo run, --output json, ramificación por código de salida
  mcp/connectors.md      Puerta 3: configuraciones listas para pegar en Claude.ai, Cursor, VS Code
  ci/gate.yml            Puerta 4: un workflow de run-pack-action para copiar a tu repo
```

## Puerta 1: REST

La versión más cruda es un solo `curl` (`curl/run.sh`): haz POST de los args a
`/api/v1/commands/{namespace}/{name}` con una clave Bearer, y lee `data.result` de vuelta.

La versión ergonómica es `python/huitzo_client.py`. Su único trabajo son los cuatro pasos, y la única sutileza que vale la pena ver es la división síncrono-contra-asíncrono:

```python
data = self._post_command(client, namespace, name, args or {})
if "task_id" in data:
    return self._poll_task(client, data["task_id"])  # long command: poll the task
return data["result"]                                 # fast command: result is right here
```

Los comandos rápidos responden en línea. Los comandos largos devuelven un `task_id` que sondeas en `/api/v1/tasks/{id}` hasta que el estado sea terminal. El cliente también respeta `Retry-After` en un 429 y expone el `correlation_id` en un error, así un fallo en tus logs coincide con una petición en los de Huitzo.

## Puerta 2: CLI

`cli/USAGE.md` muestra la misma llamada como `huitzo run @your-org/macro-snapshot/country-snapshot
--output json`, y cómo la CLI asigna desenlaces a códigos de salida (`0` éxito, `2` re-autenticar,
`4`/`5` transitorio, `10` el comando falló) para que un script de shell ramifique sin parsear.

## Puerta 3: MCP alojado

Huitzo corre un servidor MCP en `https://huitzo.ai/mcp` que expone tus comandos como herramientas,
así Claude.ai o Cursor pueden llamar a tu pack. `mcp/connectors.md` tiene las configuraciones listas para pegar;
`python/mcp_client.py` habla el JSON-RPC a mano para que veas lo que hace un conector.
El único detalle específico de Huitzo es el mapeo sin pérdidas de nombres de herramienta:

```python
to_mcp_tool_name("@reef/macro-snapshot/country-snapshot")  # -> "reef__macro-snapshot__country-snapshot"
```

La autenticación de MCP es solo por clave de API; los JWT se rechazan a propósito, porque la configuración de un conector vive en la interfaz de un cliente durante meses y necesita una credencial de larga duración, con alcance y revocable.

## Puerta 4: portón de CI

`ci/gate.yml` es una GitHub Action que copias a tu propio repo. Ejecuta un pack en cada
pull request con `huitzo-inc/run-pack-action@v1` y hace fallar el build a menos que se cumpla
una condición JSONPath. Así pones una decisión de Huitzo en el camino de un merge. (No está
activa en este repo; GitHub solo ejecuta workflows bajo el `.github/workflows/` de la raíz del repo.)

## Prueba los clientes sin Hub

Los dos archivos de prueba son el punto de este peldaño tanto como los clientes. Simulan las
capas HTTP y de transporte (con `respx`), así que prueban la lógica del cliente, la desenvoltura
de la envoltura, la división síncrono-contra-asíncrono, el reintento en 429, el ida y vuelta del
nombre de herramienta, sin Hub ni clave:

```python
@respx.mock
def test_async_command_polls_until_success():
    respx.post(CMD_URL).mock(return_value=httpx.Response(200, json={"data": {"task_id": "task_1", "status": "pending"}}))
    respx.get(f"{API}/api/v1/tasks/task_1").mock(side_effect=[
        httpx.Response(200, json={"success": True, "data": {"status": "started"}}),
        httpx.Response(200, json={"success": True, "data": {"status": "success", "result": _SNAPSHOT}}),
    ])
    assert _client().execute("reef", "country-snapshot", {"country": "USA"}) == _SNAPSHOT
```

## Qué es igual por cada puerta

- **Un alcance.** Cada puerta usa una clave de API con `commands:execute`. Nada aquí puede
  publicar un pack, gestionar claves ni tocar la facturación.
- **Aislamiento de inquilino.** RLS hace cumplir que una clave solo vea y ejecute comandos que
  su inquilino tiene permitidos, de forma idéntica por REST, CLI y MCP. Un id de otro inquilino
  devuelve 404, no 403, así la API ni siquiera confirma que el comando de otro inquilino existe.
- **Ids de correlación.** Cada respuesta (y cada error) lleva un `correlation_id` que ata tus logs
  a los de Huitzo.

Cuatro puertas, una sola ejecución gobernada, auditada y aislada por RLS detrás de todas.

## Siguiente

Has construido packs, los has compuesto, le has puesto un dashboard a uno y manejado uno desde fuera.
El [Nivel 6: fullstack-triage](../06-fullstack-triage) junta el pack y el dashboard en
un solo proyecto y los prueba de principio a fin en tu portátil.
