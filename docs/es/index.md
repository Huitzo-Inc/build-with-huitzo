<!-- i18n-source-sha: 290572fdfad9e9e28cd3b063ace195a15c59a8a789bdccd99b3d9f92300d34b0 -->

# Ruta de aprendizaje

Un orden guiado para recorrer este repo. El README de cada proyecto es el tutorial completo; esta página es el mapa.

## Empieza aquí

1. **[Nivel 0: hello-pack](../../projects/00-hello-pack)**: entra texto, llamada al modelo, salida tipada. Cinco minutos. Haz esto primero.

## Nivel 1: packs de propósito único (una tarde cada uno)

2. **`01a-doc-to-json`**: lee un documento y devuelve campos tipados.
3. **`01b-macro-snapshot`**: llama a una API pública y devuelve un resumen fundamentado.
4. **`01c-inbox-triage`**: el triaje determinista decide la urgencia; el modelo solo redacta una respuesta, y el pack nunca envía.
5. **`01d-daily-digest`**: un CSV de ventas se convierte en un resumen y una alerta de anomalía.

## Nivel 2: packs gobernados (unos días)

6. **`02-grounded-reco`**: lógica determinista, evaluaciones automáticas y un rastro de auditoría completo. Aquí la gobernanza se vuelve real.

## Nivel 3: composición

7. **`03-claims-pipeline`**: tres comandos tipados compuestos en un pipeline gobernado. Un flujo de trabajo es dato declarativo que el ejecutor verifica por tipos.

## Nivel 4: construye un frontend

8. **`04-first-dashboard`**: un dashboard de React que llama a un pack desde el navegador con `useCommand`. El frontend es un consumidor delgado de decisiones que el pack ya tomó. Corre localmente sin Hub.

## Nivel 5: interactúa con huitzo.ai desde fuera

9. **`05-pack-from-outside`**: maneja un pack desplegado por REST, la CLI, el servidor MCP alojado y CI. Un solo modelo mental, cuatro puertas.

## Nivel 6: fullstack

10. **`06-fullstack-triage`**: un pack y un dashboard en un proyecto, acoplados solo por la API de comandos y probados de principio a fin en tu portátil.

## Próximamente

- **Nivel 7: `07-sovereign-suite`**: un sistema gobernado, multiinquilino y desplegable en cualquier entorno para un conglomerado. La cima alcanzable, donde cada peldaño anterior se compone hacia arriba. Registrado como un issue de GitHub; dale una estrella al repo para seguir el avance.

## Para profundizar

Este repo contiene los tutoriales prácticos. Para referencia de API y explicación conceptual, visita [docs.huitzo.ai](https://docs.huitzo.ai/docs/).
