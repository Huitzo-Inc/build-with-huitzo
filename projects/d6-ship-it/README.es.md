<!-- i18n-source-sha: 3cac499bf86d4fdc6e74667ddfe1264d1d1f1434c90601bd683c67d344eac394 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Dashboard D6: ship-it

> Read this in [English](./README.md).

Todos los demás peldaños terminan en "ejecútalo localmente". Este trata del paso siguiente: llevar un dashboard a un Hub real sin descubrir el problema cuando ya está publicado.

La idea que hay que llevarse de aquí: **casi todo despliegue fallido es un error que podrías haber detectado sin conexión.** Una versión que se desincronizó entre dos archivos, un comando que llamas pero nunca declaraste, un bundle que compiló perfectamente y olvidó exportar la única función que Hub llama. Ninguno de esos necesita una cuenta de Hub para encontrarse: necesitan que alguien mire. `scripts/preflight.mjs` es ese alguien.

**Aprenderás:** qué promete realmente el manifiesto del dashboard a Hub, por qué `pack_dependencies` no es documentación, el ciclo de publicación (`validate` → `build` → `publish`), cómo versionar contra un contrato de comandos, y cómo escribir un preflight que puedas copiar en cada proyecto que publiques.

**Tiempo:** unos treinta minutos.

## Requisitos previos

- Node 20+ y npm
- [D0: `d0-hello-dashboard`](../d0-hello-dashboard) para el contrato `mount`/`unmount`
- Una cuenta de Hub solo para los dos últimos comandos. Todo lo anterior corre sin conexión.

## Ejecútalo

```bash
cd dashboard
npm install
npm test            # 8 pruebas: la vista, incluidos los estados gobernados
npm run preflight   # construye y luego comprueba todo lo que publish rechazaría
```

El preflight pasa con un aviso, a propósito:

```
⚠  namespace is still "reef"
   The examples are scoped to an org you do not own. Change it before publishing for real.
✔  preflight passed for reef/ship-it@0.1.0 (1 warning(s)).
   Next: huitzo dashboard validate && huitzo dashboard publish
```

Ese aviso es lo primero que arreglas cuando esto pasa a ser tu dashboard y no un ejemplo.

## Qué promete el manifiesto

`huitzo-dashboard.yaml` no es una descripción. Cada campo es una promesa de la que Hub depende:

| Campo | Qué hace Hub con él |
|---|---|
| `name` + `namespace` | La identidad bajo la que publica. Juntos son la dirección. |
| `version` | Ordena las versiones. Debe ser semver y coincidir con `package.json`. |
| `pack_dependencies` | Muestra los "packs requeridos" en la página de Explorar y comprueba que el inquilino los tenga. |
| `build.entry_point` | El archivo que importa y sobre el que llama a `mount()`. |
| `build.min_sdk_version` | Se niega a cargar el dashboard en un Hub más antiguo. |

## Las siete comprobaciones

`scripts/preflight.mjs` no tiene dependencias y tarda alrededor de un segundo. Cópialo a cualquier dashboard y funciona sin cambios.

**1. El manifiesto existe y trae sus campos obligatorios.** Hub no puede indexar un dashboard sin `name`, `namespace` y `version`.

**2. La versión es semver.** Hub ordena las versiones por ella. `v1` no se puede ordenar.

**3. `package.json` y el manifiesto coinciden en esa versión.** Cada uno lleva la suya, y se desincronizan la primera vez que alguien sube una y olvida la otra. Entonces la versión que Hub muestra no es la que construiste, y no lo notarás, porque nada da error.

**4. Todo comando que llama el código tiene su pack declarado.** Esta es la comprobación que justifica el script:

```js
// Un id de comando es solo una cadena, así que nada impide llamar a un pack
// que nunca declaraste. Compila. Las pruebas pasan. Hub no sabe que lo necesitas.
if (!declared.has(pack)) fail(`the code calls ${id} but ${pack} is not in pack_dependencies`);
```

**5. Un pack declarado que nunca se llama es un aviso.** Las dependencias obsoletas hacen que tu dashboard parezca necesitar más de lo que necesita.

**6. El bundle construido exporta de verdad `mount` y `unmount`.** La forma más común de que un dashboard compile limpio y luego se niegue a cargar. Ni `tsc` ni vitest miran nunca dentro de `dist/`, así que nada más lo detecta:

```js
const mod = await import(pathToFileURL(distPath).href);
for (const fn of ["mount", "unmount"]) {
  if (typeof mod[fn] !== "function") fail(`the bundle does not export ${fn}()`);
}
```

**7. Publicas en una org que posees.** Un aviso mientras `namespace: reef`.

Cada una de ellas se verificó rompiéndola a propósito y observando fallar la comprobación correcta: una compuerta que nadie ha visto fallar no es una compuerta.

## Luego publica

```bash
huitzo dashboard validate     # comprobación completa de esquema, reglas del servidor
huitzo dashboard build        # ejecuta npm run build
huitzo dashboard publish      # sube dist/main.js como una versión nueva
```

`validate` y el preflight se solapan deliberadamente. El preflight es tuyo, corre sin conexión en un segundo y puede comprobar cosas que solo tú sabes (que tus ids de comando coinciden con tu código). `validate` es de la plataforma, y es la autoridad.

Luego ábrelo desde Hub en `https://hub.huitzo.com/d/ship-it`. No hay URLs separadas para dashboards; Hub es el único punto de entrada y tu dashboard comparte su sesión.

> Vuelve a asignarlo primero: cambia `namespace:` en `huitzo-dashboard.yaml` a una org que poseas, y los ids de comando en `src/types.ts` para que coincidan. Consulta [Ejecuta en tu propio Hub](../../README.es.md#ejecuta-en-tu-propio-hub).

## Versionar contra un contrato de comandos

El dashboard y el pack se publican a su propio ritmo, acoplados solo por el id del comando y la forma del resultado. Eso te da una regla simple:

- El pack cambia sus **internos**: nada que hacer. Ese es todo el sentido del contrato.
- El pack **añade** un campo opcional: nada que hacer. Tu `types.ts` es un subconjunto; los campos extra se ignoran.
- El pack **renombra o elimina** un campo que renderizas, o cambia un id de comando: eso es un cambio incompatible en el contrato. Sube la versión del dashboard y fija `pack_dependencies` a un rango que excluya el pack antiguo.

`version: "*"` en `pack_dependencies` está bien para un ejemplo. Para algo real, fíjala, porque `"*"` significa "cualquier versión, incluida la que te rompió".

## Por qué la interfaz aquí muestra la gobernanza

El panel renderiza un resultado de `recommend` de [`02-grounded-reco`](../02-grounded-reco), y trata `withheld` y `escalated` como **estados de primera clase, no como errores**. Un pack gobernado que retiene un resultado no ha fallado: ha hecho exactamente su trabajo, y la interfaz tiene que decirlo en vez de mostrar un panel en blanco o un aviso rojo.

Eso es un adelanto de D5, que construye la interfaz gobernada completa: `TemplateFrame`, `ResultSection` y un `EvidenceLink` al registro de auditoría.

## Siguiente

Con esto termina la Fase 1 de la ruta de dashboards. Los peldaños restantes (formularios declarativos, comandos en streaming y encolados, y la interfaz gobernada) están listados en [la ruta de aprendizaje](../../docs/es/index.md#la-ruta-de-dashboards). El peldaño final que ambas rutas comparten es [`06-fullstack-triage`](../06-fullstack-triage).
