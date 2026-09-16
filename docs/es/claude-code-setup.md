<!-- i18n-source-sha: 702b81a9a7ecd8fdfa380ff8d03f8f050c32e0c9421a4bb7f945b3bf8f29fbf3 -->

# Construye con un agente de IA

> **Guía ilustrada:** los mismos pasos con capturas de pantalla están en
> [la guía de instalación paso a paso](https://huitzo-my.sharepoint.com/:w:/g/personal/ernesto_huitzo_ai/IQBmjQk-U-pCRqonwrt9o7_CAQv1gfp3ruaT6oji1uEAX5w?e=549vuB).
> Si prefieres solo los comandos, todo lo que necesitas está en esta página.

Cada proyecto de este repo está escrito para que lo lea una persona *y* para que
un agente de IA construya sobre él. [`pack-claude-env`](https://github.com/Huitzo-Inc/pack-claude-env)
es el entorno de desarrollo de Huitzo para [Claude Code](https://code.claude.com/docs/en/overview):
le entrega a tu agente referencias de API verificadas, un flujo de trabajo
docs-first, agentes revisores y hooks de seguridad, para que el código que escriba
se parezca al código de este repo.

Este paso es **opcional**. Todos los peldaños de aquí funcionan sin él. Pero en
cuanto dejas de copiar ejemplos y empiezas a escribir tu propio pack, esto es lo
que evita que un agente invente un SDK que no existe.

**Tiempo:** unos cinco minutos.

## Qué te da

| | Qué hace |
|---|---|
| **Skills de referencia** | Superficies de API exactas y fijadas por versión para `huitzo-sdk`, `huitzo.yaml`, el SDK de dashboards, la CLI y la API REST de la plataforma. El agente lee la firma real en vez de adivinar. |
| **Skills de flujo de trabajo** | `/draft-spec`, `/draft-docs`, `/add-command`, `/scaffold-dashboard`, `/test-pack`, `/validate-pack`, `/test-dashboard`, `/dashboard-dev`, `/sandbox`, `/publish`. |
| **Agentes** | `pack-developer` y `dashboard-developer` para construir; `pack-reviewer` y `dashboard-reviewer` para calificar el resultado contra una lista de verificación; `docs-writer`, `spec-architect`. |
| **Reglas por ruta** | Reglas que se cargan solo cuando se edita un archivo que coincide: patrones del SDK, manejo de errores, pruebas, el manifiesto, trazabilidad, contrato con Hub, patrones de React, diseño de dashboards. |
| **Hooks de seguridad** | Un escaneo bloqueante de secretos al escribir, más avisos no bloqueantes por cabeceras de trazabilidad faltantes, colores hex en dashboards, un `model=` fijo en `ctx.llm` y `dangerouslySetInnerHTML`. |

Ese aviso sobre `model=` es la tesis completa del repo aplicada a cada pulsación
de tecla: un pack pide un **perfil**, nunca un modelo con nombre. Ver
[El momento "ajá"](./the-aha-moment.md).

## Instálalo como plugin de Claude Code (recomendado)

Dentro de Claude Code, ejecuta estos dos comandos:

```text
/plugin marketplace add Huitzo-Inc/pack-claude-env
/plugin install huitzo@huitzo
```

Luego abre un directorio de pack, dashboard o proyecto y ejecuta:

```text
/huitzo:huitzo-init
```

`huitzo-init` **te muestra un plan y pregunta antes de escribir nada.** Agrega las
reglas por ruta a `.claude/rules/`, un bloque gestionado a `CLAUDE.md` y
`AGENTS.md`, y `CONSTITUTION.md`. Si el proyecto tiene un directorio `docs/`,
también registra el servidor MCP `pack-docs` en `.mcp.json`. Nunca sobrescribe un
archivo existente y nunca toca `settings.json`.

Las skills quedan disponibles como `/huitzo:<skill>`; los agentes y hooks se
activan en cuanto el plugin está habilitado.

### Pruébalo en este repo

La forma más rápida de ver la diferencia es apuntarlo a un peldaño que ya
terminaste:

```text
cd projects/00-hello-pack/pack
/huitzo:huitzo-init
```

Luego pídele al agente que agregue un segundo comando. Observa cómo lee la skill
de referencia de `huitzo-sdk` antes de escribir, genera el modelo de argumentos y
la prueba junto al comando, y lo registra en `huitzo.yaml`: la misma forma que el
comando que ya está ahí.

## O deja que la CLI de Huitzo lo siembre

Si estás empezando un proyecto nuevo en vez de trabajar en este repo, la CLI
ofrece el mismo entorno mientras genera el andamiaje:

```bash
huitzo pack new my-pack          # → "¿Quieres configurar un entorno de Claude Code?" → sí
huitzo dashboard new my-dash     # la misma pregunta
huitzo project init my-project   # sembrado en silencio (pack + dashboard)
```

La CLI copia el entorno en el directorio `.claude/` del proyecto, filtrado por
perfil, y coloca `CONSTITUTION.md` junto a él. Las skills quedan disponibles como
`/<skill>` (sin el prefijo `huitzo:` en este canal). Ejecuta `/huitzo-init` una
vez para conectar el servidor MCP de documentación del proyecto.

Tres perfiles deciden qué se siembra: `full-stack` (el predeterminado),
`pack-only` y `dashboard-only`.

> **Elige un solo canal por proyecto.** El plugin y la semilla funcionan ambos,
> pero si instalas los dos, los hooks se ejecutan dos veces.

## ¿Aún no tienes la CLI?

```bash
# macOS / Linux / WSL2
curl -sSf https://raw.githubusercontent.com/Huitzo-Inc/huitzo-launcher/main/install.sh | sh
```

```powershell
# Windows (PowerShell)
iwr -useb https://raw.githubusercontent.com/Huitzo-Inc/huitzo-launcher/main/install.ps1 | iex
```

macOS es solo Apple Silicon; Homebrew también funciona:
`brew install Huitzo-Inc/tap/huitzo`.

## Mantenerlo al día

```text
/plugin update huitzo
/huitzo:huitzo-init     # refresca los bloques gestionados y las reglas
```

Los archivos existentes nunca se sobrescriben, así que para recibir una versión
nueva de una regla, borra tu copia de ese archivo y vuelve a ejecutar
`huitzo-init`. En el canal de semilla, vuelve a ejecutar `/huitzo-init` o copia
`claude/` desde un clon nuevo sobre `.claude/`.

## Dos servidores MCP distintos

No los confundas:

- **`pack-docs`** (local al proyecto) sirve *tu propio* directorio `docs/` al
  agente. `/huitzo-init` lo escribe en `.mcp.json` cuando existe `docs/`. Necesita
  `pip install "your-docs-mcp==1.1.2" "mcp<2"` en el entorno del proyecto.
- **El servidor de documentación alojado en Hub**, configurado con
  `huitzo mcp setup docs`, sirve la documentación de *la plataforma* en tus
  ajustes de Claude a nivel de usuario.

Un tercero, `@huitzo/dashboard-mcp`, expone los comandos, primitivas y tokens de
marca de un dashboard a cualquier cliente compatible con MCP: útil en los
peldaños de dashboards.

## Siguiente

Ve a construir algo: [Nivel 0: hello-pack](../../projects/00-hello-pack) si estás
empezando, o la [ruta de aprendizaje](./index.md) para el mapa completo.
