<!-- i18n-source-sha: ad8061979d497e1eb35d550b7ccae4add38e019ce3ee0352faf3a37a6908e888 -->

# Ruta de aprendizaje

Un orden guiado para recorrer este repo. El README de cada proyecto es el tutorial completo; esta página es el mapa.

Cada peldaño de abajo se construye y se prueba en tu portátil, sin cuenta de Hub y sin clave de API.

## Antes de empezar (opcional, cinco minutos)

- **[Construye con un agente de IA](./claude-code-setup.md)**: instala el entorno de desarrollo de Huitzo para Claude Code. Le da a tu agente referencias verificadas del SDK, el flujo de trabajo docs-first y agentes revisores, para que el código que escriba coincida con los patrones de este repo. Es opcional, pero es la vía más rápida para pasar de estos ejemplos a tu propio pack.

## Empieza aquí

1. **[Nivel 0: hello-pack](../../projects/00-hello-pack)** (~5 min): entra texto, llamada al modelo, salida tipada. Haz esto primero.

## Nivel 1: packs de propósito único (~10 minutos cada uno)

2. **[`01a-doc-to-json`](../../projects/01a-doc-to-json)**: lee un documento y devuelve campos tipados.
3. **[`01b-macro-snapshot`](../../projects/01b-macro-snapshot)**: llama a una API pública y devuelve un resumen fundamentado.
4. **[`01c-inbox-triage`](../../projects/01c-inbox-triage)**: el triaje determinista decide la urgencia; el modelo solo redacta una respuesta, y el pack nunca envía.
5. **[`01d-daily-digest`](../../projects/01d-daily-digest)**: un CSV de ventas se convierte en un resumen y una alerta de anomalía.

## Nivel 2: packs gobernados (~15 minutos)

6. **[`02-grounded-reco`](../../projects/02-grounded-reco)**: lógica determinista, evaluaciones automáticas y un rastro de auditoría completo. Aquí la gobernanza se vuelve real. Acompáñalo con [El momento "ajá"](./the-aha-moment.md).

## Nivel 3: composición (~30 minutos)

7. **[`03-claims-pipeline`](../../projects/03-claims-pipeline)**: tres comandos tipados compuestos en un pipeline gobernado. Un flujo de trabajo es dato declarativo que el ejecutor verifica por tipos.

## Nivel 4: construye un frontend (~40 minutos)

8. **[`04-first-dashboard`](../../projects/04-first-dashboard)**: un dashboard de React que llama a un pack desde el navegador con `useCommand`. El frontend es un consumidor delgado de decisiones que el pack ya tomó. Corre localmente sin Hub.

> **¿Eres desarrollador de front-end?** No tienes que subir toda la escalera primero. Este peldaño solo necesita [`01b-macro-snapshot`](../../projects/01b-macro-snapshot) como el pack al que llama, así que el camino corto hasta una interfaz funcionando es **Nivel 0 → `01b` → Nivel 4 → Nivel 6**.

## Nivel 5: interactúa con huitzo.ai desde fuera (~40 minutos)

9. **[`05-pack-from-outside`](../../projects/05-pack-from-outside)**: maneja un pack desplegado por REST, la CLI, el servidor MCP alojado y CI. Un solo modelo mental, cuatro puertas.

## Nivel 6: fullstack (~1 hora)

10. **[`06-fullstack-triage`](../../projects/06-fullstack-triage)**: un pack y un dashboard en un proyecto, acoplados solo por la API de comandos y probados de principio a fin en tu portátil.

## Soluciones de referencia para sectores regulados

No son un peldaño de la escalera. Llevan el patrón gobernado hasta el final en un sector regulado concreto, como punto de partida creíble para un entregable real de cliente, pensado para adaptarse y revenderse.

- **[`08-trade-surveillance`](../../projects/08-trade-surveillance)**: examina operaciones en busca de patrones de abuso de mercado, con detección determinista, una narrativa de analista escrita por el modelo, una evaluación de fundamentación y un registro de auditoría completo.

## Próximamente

- **Nivel 7: `07-sovereign-suite`**: un sistema gobernado, multiinquilino y desplegable en cualquier entorno para un conglomerado. La cima alcanzable, donde cada peldaño anterior se compone hacia arriba. Dale una estrella al repo para seguir el avance.

## Para profundizar

Este repo contiene los tutoriales prácticos. Para referencia de API y explicación conceptual, visita [docs.huitzo.ai](https://docs.huitzo.ai/docs/).
