<!-- i18n-source-sha: 495020f191d286ec747f4c6224fce0cc8c3e827abca3ade3fb65d7620f3b16eb -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Dashboard D0: hello-dashboard

> Read this in [English](./README.md).

Lo más pequeño que Huitzo Hub puede cargar. Sin pack, sin llamada a comandos, sin red, sin Python. Hub le entrega a tu módulo un nodo del DOM y un objeto de contexto, y tú renderizas. Si haces una sola cosa en la ruta de dashboards, haz esta.

La idea que hay que llevarse de aquí: **un Dashboard de Huitzo no es un sitio web, es un módulo que Hub monta dentro de sí mismo.** No hay servidor tuyo, ni router, ni URL aparte. Hub es dueño de la página; tú eres dueño de un subárbol de ella.

**Aprenderás:** el contrato `mount`/`unmount`, por qué tu dashboard trae su propia raíz de React y su propio límite de errores, cómo `useHubContext` te da la sesión y el tema antes de pedir nada, y cómo correr todo esto en tu portátil sin Hub alguno.

**Tiempo:** unos diez minutos.

## Requisitos previos

- Node 20+ y npm

Esa es toda la lista. Sin cuenta de Hub, sin CLI, sin Python y sin pack.

## Ejecútalo

```bash
cd dashboard
npm install
npm test            # 5 pruebas, sin navegador y sin Hub
npm run build       # verifica tipos y luego empaqueta dist/main.js
```

Para verlo en un navegador:

```bash
npm run dev         # http://localhost:3000
```

No hay servidor simulado que arrancar, porque este peldaño nunca llama a un comando. Todo lo que ves en pantalla vino del objeto de contexto, que es precisamente el punto.

## Qué hay dentro

```
dashboard/
  huitzo-dashboard.yaml    el manifiesto: identidad y build (sin dependencias de packs)
  package.json             React 19 + los dos paquetes del SDK de Huitzo
  vite.config.ts           build en modo librería (-> dist/main.js) + la config de pruebas
  index.html               host de desarrollo; carga src/dev.tsx
  src/
    main.tsx               entrada de PRODUCCIÓN: exporta mount() / unmount()   <- la lección
    dev.tsx                entrada de DESARROLLO: construye un contexto falso y llama a mount()
    App.tsx                toda la interfaz, un componente
    components/
      ErrorBoundary.tsx    un dashboard tiene su propio límite de errores
    main.test.tsx          prueba el contrato de mount
```

Copia `vite.config.ts` y `tsconfig.json` hacia adelante en cada dashboard que escribas. Son idénticos en todos los peldaños, y esta es la última vez que tienes que pensar en ellos.

## El contrato son dos funciones

Lo único que importa de `src/main.tsx`:

```tsx
export function mount(container: HTMLElement, context: HuitzoContext): void {
  const root = createRoot(container);
  roots.set(container, root);
  root.render(
    <ErrorBoundary>
      <HuitzoProvider context={context}>
        <App />
      </HuitzoProvider>
    </ErrorBoundary>,
  );
}

export function unmount(container: HTMLElement): void {
  roots.get(container)?.unmount();
  roots.delete(container);
}
```

Cuatro cosas a notar:

1. **Tú creas tu propia raíz de React.** Hub no te da una. Eso es lo que permite que tu dashboard empaquete su propia versión de React sin pelear con la de Hub.
2. **Envuelves la app en tu propio `ErrorBoundary`.** Un fallo de renderizado dentro de tu dashboard debe quedarse dentro de tu dashboard. Los hooks no pueden capturar errores de renderizado, así que este es el único lugar donde todavía hace falta un componente de clase.
3. **`HuitzoProvider` toma el contexto** y lo pone a disposición de cada hook debajo. Sin él, `useHubContext` no tiene nada que leer.
4. **`unmount` tiene que limpiar de verdad.** Hub reutiliza nodos contenedores. El `WeakMap` indexado por contenedor es cómo `unmount` encuentra la raíz correcta, y por qué un contenedor desprendido todavía puede ser recolectado por el recolector de basura.

## El contexto llega antes de cualquier petición

`App.tsx` llama a un hook y ya sabe quién inició sesión:

```tsx
const { user, theme, dashboardSlug } = useHubContext();
```

No se hizo ninguna petición. Hub pasó todo eso a `mount()`, porque tu dashboard comparte la sesión de Hub: el mismo JWT, el mismo usuario, el mismo inquilino. Nunca construyes una pantalla de inicio de sesión.

`useHubContext` además es **reactivo**. Cambia el tema en Hub y `theme` cambia y tu componente se vuelve a renderizar. No es una foto tomada en el momento del montaje.

## Se aplica el tema solo

`main.tsx` importa los tokens de diseño del SDK exactamente una vez:

```tsx
import "@huitzo/dashboard-sdk-react/styles";
```

Después de eso, `hz-card`, `hz-eyebrow`, `hz-stat__number`, `hz-btn--ghost` y `var(--color-*)` resuelven. **No hay ni un solo color hex en este proyecto.** Eso es el requisito, no un detalle bonito: como cada color pasa por un token, un Hub de marca blanca reestiliza tu dashboard sin cambiar una línea, y el modo claro funciona sin que tú lo escribas.

Abre `index.html` y cambia `data-theme="dark"` por `"light"`. Todo debería seguir viéndose intencional. Si algo se ve deslavado o invisible, tienes un color fijo en alguna parte.

## Prueba el contrato, no el texto

`npm test` corre cinco pruebas, y ninguna comprueba lo que dice la página. Comprueban de qué depende Hub:

```tsx
it("empties the container on unmount, so Hub can reuse the node", () => {
  const container = document.createElement("div");
  act(() => mount(container, makeContext()));
  expect(container.innerHTML).not.toBe("");

  act(() => unmount(container));
  expect(container.innerHTML).toBe("");
});
```

Un dashboard que renderiza precioso pero tiene fugas al desmontarse romperá Hub en la segunda visita. Prueba el contrato primero; la interfaz es la parte fácil.

## Ejecútalo de verdad

> Vuelve a asignarlo primero: el ejemplo usa la org `@reef`, que no es tuya. Cambia `namespace:` en `huitzo-dashboard.yaml` a una org que sí poseas. Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub).

Cuando tengas una cuenta de Hub en modo desarrollador:

```bash
huitzo dashboard validate
huitzo dashboard build      # ejecuta npm run build
huitzo dashboard publish    # sube dist/main.js como una versión nueva
```

Luego ábrelo desde Hub en `https://hub.huitzo.com/d/hello-dashboard`. No hay URLs separadas para dashboards; Hub es el único punto de entrada.

## Siguiente

Tu dashboard se monta, pero todavía no hace nada. [Nivel 4: `04-first-dashboard`](../04-first-dashboard) lo apunta a un comando real de un pack con `useCommand`, y a un Hub simulado para que siga corriendo en tu portátil.
