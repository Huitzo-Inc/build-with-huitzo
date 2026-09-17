<!-- i18n-source-sha: c9f41da181be89acd8e3a703f19408bb14b004584e8eb5b81627eb23b6e2ddfa -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 4: first-dashboard

> Read this in [English](./README.md).

Has construido packs. Ahora ponle cara a uno. Este es un dashboard de React que corre dentro de Huitzo Hub y llama al pack `macro-snapshot` desde el navegador: eliges un país y un indicador, pulsas Run, y vuelve la instantánea fundamentada del pack. No escribes backend propio.

La idea que hay que llevarse de aquí: **el dashboard es un consumidor delgado de decisiones que Python ya tomó.** Cada número en pantalla se calculó en Python determinista dentro del pack. El único trabajo del dashboard es llamar a un comando y renderizar el resultado tipado. Nunca habla con un modelo y nunca hace los cálculos.

**Aprenderás:** el contrato `mount`/`unmount` que convierte un dashboard en una app de Hub, cómo `useCommand` transforma un comando de pack en `{execute, data, loading, error}`, cómo el dashboard hereda el tema de Hub a través de los tokens de diseño, y el truco que deja correr todo esto en tu portátil sin Hub alguno.

**Tiempo:** unos cuarenta minutos.

## Requisitos previos

- Node 20+ y npm
- Cualquiera de las dos rutas de entrada: en la escalera de packs llegas desde el [Nivel 3](../03-claims-pipeline); en la [ruta de dashboards](../../docs/es/index.md#la-ruta-de-dashboards) este peldaño es **D1** y llegas desde [D0: `d0-hello-dashboard`](../d0-hello-dashboard), que cubre el contrato `mount`/`unmount` que este README da por sabido.
- Útil pero no obligatorio: [`01b-macro-snapshot`](../01b-macro-snapshot), el pack al que llama este dashboard. No necesitas construirlo: el servidor simulado lo sustituye, y aquí nunca escribes Python.
- No necesitas cuenta de Hub para construir, probar o ejecutar esto localmente. Un Hub con el pack desplegado solo hace falta para publicarlo de verdad.

## Ejecútalo

```bash
cd dashboard
npm install
npm test            # 8 pruebas, sin navegador y sin Hub
npm run build       # verifica tipos y luego empaqueta dist/main.js (exporta mount/unmount)
```

Para verlo en un navegador con un Hub falso, abre dos terminales:

```bash
node mock-server.mjs   # terminal 1: un sustituto diminuto de la API de Hub en :8787
npm run dev            # terminal 2: sirve el dashboard en :3000
```

Abre `http://localhost:3000`, elige un país y pulsa Run. La llamada va al servidor simulado, no a un Hub real. Ese bucle local es el centro de este peldaño, y se explica más abajo.

## Qué hay dentro

```
dashboard/
  huitzo-dashboard.yaml          el manifiesto: identidad, el pack del que depende, el build
  package.json                   React 19 + los dos paquetes del SDK de Huitzo
  vite.config.ts                 build en modo librería (-> dist/main.js) + la config de pruebas
  index.html                     host de desarrollo; carga src/dev.tsx
  mock-server.mjs                una API de Hub falsa y diminuta para desarrollo local
  src/
    main.tsx                     entrada de PRODUCCIÓN: exporta mount() / unmount()
    dev.tsx                      entrada de DESARROLLO: construye un contexto de Hub falso y llama a mount()
    App.tsx                      maquetado: encabezado + panel
    types.ts                     el id del comando y la forma del resultado (el contrato del pack)
    components/
      SnapshotPanel.tsx          contenedor: conecta useCommand con la vista
      SnapshotView.tsx           presentación: pura, recibe props, fácil de probar
      HubHeader.tsx              useHubNavigation + useHubContext
      ErrorBoundary.tsx          un dashboard tiene su propio límite de errores
    SnapshotView.test.tsx        renderiza cada estado a partir de props simples
    App.test.tsx                 prueba de humo con los hooks del SDK simulados
```

## El contrato mount

Un Dashboard de Huitzo no es un sitio web. Es un módulo que Hub carga y ejecuta dentro de sí mismo. El contrato son dos funciones, en `src/main.tsx`:

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

Hub llama a `mount()` con un nodo del DOM y un `HuitzoContext` (la sesión JWT compartida, el usuario, la navegación). Tú creas tu **propia** raíz de React y envuelves la app en tu **propio** `ErrorBoundary`, así un fallo en tu dashboard queda contenido y nunca tumba a Hub. `HuitzoProvider` toma ese contexto y lo pone a disposición de cada hook debajo.

## Llamar a un pack con `useCommand`

Este es el punto central. Un hook convierte un comando de pack en una máquina de estados lista para renderizar (`src/components/SnapshotPanel.tsx`):

```tsx
const { execute, data, loading, error } = useCommand<CountrySnapshot>(
  "@reef/macro-snapshot/country-snapshot",
);
// ...
onRun={() => void execute({ country, indicator })}
```

`execute(args)` ejecuta el comando en el Hub. `loading` es verdadero mientras está en vuelo, `error` contiene un `HuitzoError` tipado si falla, y `data` es el `CountrySnapshot` tipado si tiene éxito. El dashboard no comparte código con el pack: acuerdan el id del comando y la forma del resultado (`src/types.ts` es el espejo en TypeScript del modelo Pydantic de salida del pack). Ese acoplamiento flojo es deliberado: el mismo dashboard funciona contra cualquier versión del pack que siga devolviendo esa forma.

## Presentación frente a cableado (por qué probar es fácil)

Fíjate en la separación: `SnapshotPanel` tiene el hook, y `SnapshotView` es una función pura de sus props (`loading`, `error`, `data`, `onRun`). Eso es lo que hace que la lógica de renderizado sea probable sin Hub, sin SDK y sin red:

```tsx
it("success: shows the value, the delta, and the model summary", () => {
  render(<SnapshotView {...base} data={sample} />);
  expect(screen.getByText("3.4")).toBeTruthy();
  expect(screen.getByText(sample.summary)).toBeTruthy();
});
```

`npm test` corre ocho de estas. El único lugar donde tocamos el SDK, `App.test.tsx`, simula los hooks para que la prueba siga sin necesitar Hub. La integración real con el SDK se verifica de otras dos formas: `npm run build` comprueba los tipos de cada componente contra los tipos reales del SDK, y `dev.tsx` lo ejecuta de verdad en un navegador.

## Se aplica el tema solo

El dashboard importa los tokens de diseño del SDK una vez (`import "@huitzo/dashboard-sdk-react/styles"` en `main.tsx`) y se estiliza con clases `hz-*` (`hz-card`, `hz-stat__number`, `hz-btn--primary`, `hz-eyebrow`) y tokens `var(--color-*)`. **No hay ningún hex escrito a mano.** Cuando este dashboard corre dentro de Hub, los tokens de marca de Hub ganan, así que un Hub de marca blanca reestiliza tu dashboard sin cambiar una línea. El encabezado lee el tema en vivo desde `useHubContext()`.

## Pruébalo sin Hub

En producción, Hub construye el `HuitzoContext` y llama a `mount()`. En desarrollo, `src/dev.tsx` construye un contexto falso a mano y llama a `mount()` él mismo:

```tsx
const devContext: HuitzoContext = {
  apiUrl: "http://localhost:8787",
  getToken: () => "dev-token",
  slug: "first-dashboard",
  sdkVersion: "dev",
  user: { id: "usr_dev", email: "dev@reef.example", name: "Dev", roles: ["owner"], tenantId: "ten_dev" },
  navigate: (path) => console.log("navigate ->", path),
  navigateToHub: () => alert("← Hub (mock)"),
  navigateToDashboard: (slug) => console.log("dashboard ->", slug),
  showNotification: (message, type) => console.log(`[${type}] ${message}`),
  on: () => () => {},
  emit: () => {},
};
mount(document.getElementById("root")!, devContext);
```

Apunta `apiUrl` al `mock-server.mjs` incluido, que responde la llamada al comando con una instantánea predefinida, y el dashboard corre de principio a fin en tu máquina. Así construyes e iteras un frontend de Huitzo antes de tener acceso a un Hub.

## Qué está planificado (no se usa aquí)

Este peldaño usa a propósito la porción más pequeña posible del SDK. Hay mucho más en la caja, y todo funciona hoy sobre el bus de eventos de Hub: `useRealtime`, `useHubActions`, `useHubBreadcrumbs`, `usePacks`, `useLocale`, `useStreamingCommand` (salida token a token), además de los componentes `Form`, `Dashboard`, `DashboardTile` y `TemplateFrame`. Este primer dashboard simplemente aún no los necesita.

El único hook que *no* está implementado es `useConnectionStatus`: llamarlo lanza un error claro que te remite a `useRealtime()` (la capa WebSocket de eventos de pack que necesita está diferida a una versión futura del backend).

Hay dos paquetes complementarios publicados y usables: [`@huitzo/dashboard-primitives`](https://www.npmjs.com/package/@huitzo/dashboard-primitives) (un registro de componentes `hz-*` para copiar, estilo shadcn, fijados por hash) y [`@huitzo/dashboard-mcp`](https://www.npmjs.com/package/@huitzo/dashboard-mcp) (un servidor MCP que expone los comandos, primitivas y tokens de marca de tu dashboard a un agente de IA; ver [Construye con un agente de IA](../../docs/es/claude-code-setup.md)).

## Ejecútalo de verdad

Cuando tengas una cuenta de Hub en modo desarrollador y el pack `macro-snapshot` desplegado:

```bash
huitzo dashboard validate
huitzo dashboard build      # ejecuta npm run build
huitzo dashboard publish    # sube dist/main.js como una nueva versión
```

Luego ábrelo desde tu Hub en `https://hub.huitzo.com/d/first-dashboard`. No hay URLs de dashboard separadas; Hub es el único punto de entrada, y tu dashboard comparte la sesión de Hub.

## Siguiente

Puedes construir un frontend sobre un pack. El [Nivel 5: pack-from-outside](../05-pack-from-outside) va en la otra dirección: manejar un pack desplegado desde fuera del navegador por completo, por REST, la CLI y el servidor MCP alojado.
