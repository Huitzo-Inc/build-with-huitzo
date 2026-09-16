<!-- i18n-source-sha: d3386ba21200bfa413b6a16e777f2752614aa1325ee73bbe4f47edc91f61d246 -->
<!-- Este archivo es una traducción revisada de README.md (la fuente en inglés). No lo edites a mano para corregir contenido: actualiza el inglés y vuelve a generar. Ver .translation/README.md. -->

# build-with-huitzo

**Aprende a construir sobre Huitzo creando cosas reales, un peldaño a la vez.** Esta es la forma práctica, de copiar y pegar, para pasar de un "hola mundo" de cinco minutos a un despliegue gobernado y multiinquilino, ya sea que construyas el Python que decide, el React que lo muestra, o ambos.

[![tests](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/test-packs.yml/badge.svg)](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/test-packs.yml)
[![regression-gate](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/regression-gate.yml/badge.svg)](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/regression-gate.yml)
[![i18n](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/i18n.yml/badge.svg)](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/i18n.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](./LICENSE)
[![huitzo-sdk](https://img.shields.io/pypi/v/huitzo-sdk?label=huitzo-sdk)](https://pypi.org/project/huitzo-sdk/)

> Read this in [English](./README.md). La documentación de referencia completa está en [docs.huitzo.ai](https://docs.huitzo.ai/docs/).

Huitzo es el sistema operativo de IA para empresas reguladas. La unidad que construyes y despliegas es un **Intelligence Pack**: código Python determinista que toma las decisiones, con un modelo de IA invocado solo donde aporta valor. Cada ejemplo aquí sigue ese patrón, probado en CI para que funcione al primer intento.

> ⭐ **¿Primera vez? Lee primero [El momento "ajá"](./docs/es/the-aha-moment.md)** ([English](./docs/en/the-aha-moment.md)). Un pack gobernado, con el modelo cambiado de Claude a GPT‑4o modificando una sola línea de configuración — misma decisión, misma auditoría, misma Policy Card. Es la forma más rápida de *sentir por qué* construyes una solución regulada sobre Huitzo en lugar de cablear un SDK de LLM directamente.

## Dos formas de entrar

Ambas rutas corren enteramente en tu portátil, no necesitan cuenta ni clave de API,
y terminan en el mismo lugar. Elige la que coincida con lo que construyes.

| | **Construir un pack** (Python) | **Construir un dashboard** (React) |
|---|---|---|
| **Escribes** | La lógica determinista que toma la decisión | La interfaz que una persona realmente usa |
| **Necesitas** | Python 3.11+ | Node 20+ |
| **Empieza en** | [`00-hello-pack`](./projects/00-hello-pack) — 5 min | [`d0-hello-dashboard`](./projects/d0-hello-dashboard) — 10 min |
| **Ruta completa** | [La escalera](#la-escalera), Nivel 0 → 6 | [La ruta de dashboards](#la-ruta-de-dashboards), D0 → Nivel 6 |

¿No estás seguro? Empieza por el pack. Es la más corta de las dos, y es aquello a lo
que un dashboard llama.

### Inicio rápido: tu primer pack (unos cinco minutos)

Python 3.11+ es lo único que necesitas.

```bash
# 1. Obtén los ejemplos y abre el primer pack
git clone https://github.com/Huitzo-Inc/build-with-huitzo
cd build-with-huitzo/projects/00-hello-pack/pack

# 2. Crea un entorno virtual, instala el SDK y ejecuta las pruebas
python3 -m venv .venv && source .venv/bin/activate   # macOS/Linux/WSL2
pip install -e ".[dev]"
pytest                  # las pruebas sin conexión del pack (exactamente lo que corre CI)
```

> Windows (PowerShell): `py -3 -m venv .venv`, luego `.venv\Scripts\Activate.ps1`, antes de `pip install -e ".[dev]"`.

Tres pruebas en verde significan que ya tienes un Intelligence Pack funcionando.
Ahora lee [`00-hello-pack`](./projects/00-hello-pack) para ver qué acabas de
ejecutar, y sigue la [ruta de aprendizaje](./docs/es/index.md).

### Inicio rápido: tu primer dashboard (unos diez minutos)

Node 20+ es lo único que necesitas: sin Python y sin pack.

```bash
git clone https://github.com/Huitzo-Inc/build-with-huitzo
cd build-with-huitzo/projects/d0-hello-dashboard/dashboard

npm install
npm test                # 5 pruebas: el contrato de montaje de Hub
npm run dev             # http://localhost:3000
```

Eso es un Dashboard de Huitzo real corriendo sin Hub alguno. Lee
[`d0-hello-dashboard`](./projects/d0-hello-dashboard) para ver qué acaba de pasar.

Todo en este repo corre sin conexión así. La CLI y una cuenta de Hub entran
después, cuando quieras publicar — ver [Ejecuta en tu propio Hub](#ejecuta-en-tu-propio-hub).

## Constrúyelo con un agente de IA (opcional, cinco minutos)

Si usas [Claude Code](https://code.claude.com/docs/en/overview), instala el
entorno de desarrollo de Huitzo antes de escribir tu propio pack:

```text
/plugin marketplace add Huitzo-Inc/pack-claude-env
/plugin install huitzo@huitzo
/huitzo:huitzo-init
```

Le da a tu agente referencias verificadas del SDK, skills de flujo de trabajo
docs-first, agentes revisores y un hook que detecta un nombre de modelo fijo antes
de que lo subas. Instrucciones completas, los dos canales de instalación y una
guía ilustrada: **[Construye con un agente de IA](./docs/es/claude-code-setup.md)**.

## La escalera

Cada peldaño se apoya en los anteriores, así que el proyecto más difícil es alcanzable y no un muro. Empieza donde estés.

| Peldaño | Proyecto | Qué construirás | Qué demuestra |
|---------|----------|-----------------|---------------|
| **Nivel 0** | [`00-hello-pack`](./projects/00-hello-pack) | Entra texto, una llamada al modelo, salida estructurada. Cambia de modelo con una línea de configuración. | El SDK, la interfaz única, el enrutamiento agnóstico al modelo. La ruta más rápida a un pack funcionando. |
| **Nivel 1** | [`01a-doc-to-json`](./projects/01a-doc-to-json) | Lee un PDF (siniestro, informe de laboratorio, contrato) y devuelve campos tipados. | Almacenamiento + IA + salida estructurada. La promesa de la página de inicio. |
| **Nivel 1** | [`01b-macro-snapshot`](./projects/01b-macro-snapshot) | Llama a una API pública (Banco Mundial) y devuelve un resumen fundamentado. | Integración HTTP + IA fundamentada. |
| **Nivel 1** | [`01c-inbox-triage`](./projects/01c-inbox-triage) | Lee correo, lo clasifica y redacta una respuesta para que una persona la envíe. | El triaje determinista decide la urgencia; el modelo solo redacta, y el pack nunca envía. |
| **Nivel 1** | [`01d-daily-digest`](./projects/01d-daily-digest) | Convierte un CSV de ventas en un resumen y una alerta de anomalía. | Las mismas primitivas sirven a una tienda de una sola sede y a un conglomerado. |
| **Nivel 2** | [`02-grounded-reco`](./projects/02-grounded-reco) | Una recomendación que no alucinará: lógica determinista, evaluaciones automáticas y rastro de auditoría completo. | La capa de gobernanza y la Policy Card. Donde Huitzo deja de parecer un envoltorio fino sobre un LLM. |
| **Nivel 3** | [`03-claims-pipeline`](./projects/03-claims-pipeline) | Tres comandos tipados compuestos en un pipeline gobernado. | Composición: un flujo de trabajo es dato declarativo que el ejecutor verifica por tipos, no código de pegamento. |
| **Nivel 4** | [`04-first-dashboard`](./projects/04-first-dashboard) | Un dashboard de React que llama a un pack desde el navegador. | El frontend: una app del Dashboard SDK es un consumidor delgado de decisiones que el pack ya tomó. |
| **Nivel 5** | [`05-pack-from-outside`](./projects/05-pack-from-outside) | Maneja un pack desplegado por REST, la CLI, MCP alojado y CI. | Un solo modelo mental, cuatro puertas: cómo interactuar con huitzo.ai desde cualquier lugar. |
| **Nivel 6** | [`06-fullstack-triage`](./projects/06-fullstack-triage) | Un pack y un dashboard en un proyecto, probados de principio a fin en tu portátil. | Fullstack: la API de comandos es el único contrato entre Python y la interfaz. |
| Nivel 7 | `07-sovereign-suite` | Un sistema gobernado, multiinquilino y desplegable en cualquier entorno para un conglomerado. | **Próximamente** — dale una estrella al repo para seguir el avance. |

## La ruta de dashboards

Si construyes interfaces, esta es tu ruta. Empieza con un dashboard en vez de un
pack, y cada peldaño te entrega el pack al que llama, ya escrito y ya probado:
**nunca tienes que escribir Python para terminar uno.**

| Peldaño | Proyecto | Qué construirás | Qué demuestra |
|---------|----------|-----------------|---------------|
| **D0** | [`d0-hello-dashboard`](./projects/d0-hello-dashboard) | El módulo más pequeño que Hub puede montar. Sin pack, sin red. | El contrato `mount`/`unmount`: un dashboard es un módulo que Hub ejecuta, no un sitio web. |
| **D1** | [`04-first-dashboard`](./projects/04-first-dashboard) | Un dashboard que llama a un comando real de un pack con `useCommand`, contra un Hub simulado. | El frontend es un consumidor delgado de decisiones que Python ya tomó. |
| **D2** | [`06-fullstack-triage`](./projects/06-fullstack-triage) | Leer con un hook, escribir con el cliente, actualizaciones optimistas con reversión. | La API de comandos es el único contrato entre Python y la interfaz. |

Hay más peldaños en curso: formularios declarativos, el sistema de tokens de marca,
comandos en streaming y encolados, y la interfaz gobernada que renderiza una decisión
retenida y su registro de evidencia. Consulta [la ruta de aprendizaje](./docs/es/index.md)
para el mapa.

> **¿Ya conoces los packs?** El Nivel 4 es D1. Las dos rutas son el mismo repositorio
> visto desde dos direcciones, y se encuentran en el Nivel 6.

## Soluciones de referencia reguladas

Más allá de la escalera de aprendizaje, estos son puntos de partida creíbles para un entregable real de cliente — el patrón gobernado aplicado a una vertical regulada concreta, pensado para **adaptarse y revenderse**, no solo leerse. Cada uno es autoalojado y agnóstico al modelo, así que los datos del cliente nunca salen de su frontera y nunca queda atado a un proveedor.

| Vertical | Solución | Qué hace |
|----------|----------|----------|
| **Mercados financieros** | [`08-trade-surveillance`](./projects/08-trade-surveillance) | Analiza operaciones en busca de patrones de abuso de mercado (precio fuera de mercado, marcar el cierre, spoofing, operaciones de lavado, anomalías de tamaño): detección determinista + banda de riesgo, una narrativa de analista escrita por el modelo, una evaluación de fundamento y un registro de auditoría completo — las alertas de alto riesgo o sin fundamento se escalan a una persona. |

Más verticales (banca, gobierno) siguen el mismo esqueleto; adapta los detectores y conserva la gobernanza.

## Ejecuta en tu propio Hub

Todo lo anterior corre y se prueba sin conexión. Para publicar y ejecutar un ejemplo en un Hub real, dos cosas importan.

**1. Usa una org que poseas.** Los ejemplos están bajo la org `@reef`. Es casi seguro que no posees `reef`, así que vuelve a asignar cada pack a una organización que sí poseas antes de publicar:

```bash
huitzo login
# En el huitzo.yaml del pack, cambia el namespace por el slug de tu org:
#   pack:
#     namespace: tu-org        # antes: reef
huitzo pack sync                  # reescribe los entry points de pyproject.toml desde huitzo.yaml
huitzo pack publish
huitzo run @tu-org/hello-pack/hello --args '{"text": "..."}'
```

El `namespace:` en `huitzo.yaml` es la fuente autoritativa. `huitzo pack sync` reescribe los entry points de `pyproject.toml` para que coincidan, así que nunca los editas a mano. **NO necesitas tocar el argumento `namespace=` del decorador `@command(...)`** — la plataforma toma el namespace publicado de los entry points (definidos por `huitzo.yaml` + `pack sync`), así que el valor del decorador es solo metadato y cambiar tu org no exige editarlo. (Puedes actualizarlo para que coincida por legibilidad, pero no se rompe nada si lo dejas.) Los dashboards funcionan igual: cambia `namespace` y `pack_dependencies` en `huitzo-dashboard.yaml`, y los ids de comando en el `types.ts` del dashboard, por tu org.

Obtienes una org de desarrollador al activar el Modo Desarrollador (la CLI te lo pide en tu primera publicación, o lo haces en el Hub). Tu slug de org aparece en el Hub.

**2. El despliegue debe tener lo que el pack necesita.** Un pack que llama a un modelo necesita que el registro de LLM del despliegue tenga un modelo que cumpla su piso `services.llm` (una ventana de contexto más `structured_output`). Un pack que llama a una API externa necesita una integración HTTP que coincida. [`01b-macro-snapshot`](./projects/01b-macro-snapshot) muestra cómo añadir una en el Hub.

## Ejecuta de verdad: solicita un sandbox de Hub

Cada ejercicio se construye y prueba en tu portátil sin cuenta. Para ejecutar los
peldaños finales (Niveles 4–6: dashboards, los clientes externos, el pipeline
gobernado) contra un **Hub gobernado en vivo** —y sentir la historia del cambio
de modelo y la Policy Card de principio a fin— solicita un **Hub sandbox** de
partner:

- **Solicita acceso:** empieza en [huitzo.ai](https://huitzo.ai) (acceso
  anticipado), o escribe al equipo de partners a **ernesto@huitzo.ai** con tu org
  y lo que quieres construir. Cuéntanos que vienes de `build-with-huitzo`.
- **Qué obtienes:** un Hub sandbox aislado, precableado con un modelo que cumple
  el piso `structured_output` de los packs, donde puedes hacer `huitzo publish` y
  `huitzo run` de estos ejercicios y de tus propios packs de verdad.
- **Está aislado por diseño.** Un sandbox está aislado de cualquier Hub de
  cliente —la misma frontera de cero acceso y autoalojada que obtienen tus
  propios clientes regulados. Construyes y revendes sobre esa frontera; el
  sandbox te deja sentirla primero.

## Cómo mantenemos honestos estos ejemplos

- **Cada pack se prueba en CI** contra el `huitzo-sdk` publicado, así un ejemplo roto rompe el build, no tu tarde.
- **Una [comprobación semanal de deriva del SDK](./.github/workflows/sdk-drift.yml) reconstruye cada ejemplo contra los SDK *más recientes* publicados**, ignorando el lockfile. El CI de los pull requests es reproducible (instala lo que fija el lockfile), lo que significa que no puede detectar una nueva versión mayor del SDK publicada aguas arriba. Este trabajo sí puede, así que un ejemplo que deja de compilar es problema nuestro antes que tuyo.
- **Una [puerta de regresión](./tests/README.md) protege cada clase de bug que hemos corregido.** Una prueba offline por cada bug de producción pasado (fiabilidad de enums, refs de pipeline, fallos de `process` en dashboards, formas de petición de los clientes, …) corre en cada cambio, así un bug corregido nunca puede volver en silencio. Ningún ejercicio se publica si no se mantiene en verde.
- **El inglés es la única fuente de verdad; el español es una traducción revisada.** Una [verificación de obsolescencia](./.translation/README.md) impide que cualquier archivo en español quede desactualizado respecto a su fuente en inglés. Solo editas a mano el inglés.
- **Los nombres ficticios son inventados.** Empresas como Nautilus Mutual y Leviathan Holdings son marcadores de posición. No aparece ningún cliente real.

## Qué necesitas

**Para construir y probar cada ejercicio:**

- Python 3.11+ y `pip`
- Node 20+ y npm para los peldaños de dashboard (Niveles 4 y 6)
- El [`huitzo-sdk`](https://pypi.org/project/huitzo-sdk/) de PyPI (se instala por pack, con el inicio rápido de arriba)

**Solo cuando quieras publicar o ejecutar contra un Hub real:**

- La [CLI de Huitzo](https://github.com/Huitzo-Inc/huitzo-launcher) ([comandos de instalación](./docs/es/claude-code-setup.md#aún-no-tienes-la-cli)) — funciona de forma nativa en Windows, macOS (Apple Silicon), Linux y WSL2. El **runner** de Studio (no la CLI) necesita WSL2 en Windows.
- Acceso anticipado a un Huitzo Hub. Cada ejercicio se construye y se prueba localmente sin uno.

**Opcional:** [Claude Code](https://code.claude.com/docs/en/overview) más el [entorno de desarrollo de Huitzo](./docs/es/claude-code-setup.md), si quieres un agente de IA que ya conozca el SDK.

## Cómo contribuir

Los nuevos packs son bienvenidos, en especial plantillas de la comunidad. Consulta [CONTRIBUTING.md](./CONTRIBUTING.md) y busca issues con la etiqueta `good first issue`. Los reportes de seguridad van a [SECURITY.md](./SECURITY.md).

## Licencia

[MIT](./LICENSE). Construye sobre esto con libertad.
