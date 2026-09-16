<!-- i18n-source-sha: 34a68e00137f2b2d98248e1ab060b6ca0ee677085de0c343e21781070204e4c2 -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Dashboard D3: design-system

> Read this in [English](./README.md).

La misma instantánea macro, renderizada dos veces. Una versión es lo que escribe un asistente de IA cuando nadie le habla del sistema de diseño. La otra es la misma información sobre los tokens de marca de Huitzo, sin ni una sola decisión de color propia. Alterna entre ambas en el navegador y la diferencia es inmediata.

La idea que hay que llevarse de aquí: **un dashboard de Huitzo debería verse como Huitzo en el primer renderizado, no después de que alguien lo rediseñe a mano.** Eso no es cuestión de gusto: es una propiedad que obtienes gratis por no inventar nunca un color, y que pierdes en cuanto inventas uno.

**Aprenderás:** el sistema de tokens de marca y por qué sobrevive a la marca blanca, las primitivas `hz-*`, la jerarquía tipográfica de tres niveles, el presupuesto de acento, y cómo convertir las reglas de diseño en una prueba que rompe el build en vez de un documento que nadie lee.

**Tiempo:** unos treinta minutos.

## Requisitos previos

- Node 20+ y npm
- [D0: `d0-hello-dashboard`](../d0-hello-dashboard) para el contrato `mount`/`unmount`

Sin Hub, sin pack, sin red. Este peldaño renderiza una muestra fija para que la lección se mantenga en el diseño.

## Ejecútalo

```bash
cd dashboard
npm install
npm test            # 14 pruebas, 9 de ellas son las reglas de diseño mismas
npm run build
npm run dev         # http://localhost:3000 — luego usa el conmutador Branded / Generic
```

## Qué hay dentro

```
dashboard/
  src/
    sample.ts                el CountrySnapshot que ambas vistas renderizan (del pack de D1)
    App.tsx                  el conmutador
    views/
      GenericView.tsx        ❌ el antes: hex elegidos a mano, CTA con degradado, sin jerarquía
      BrandedView.tsx        ✅ el después: los mismos datos, solo tokens y hz-*
    design-rules.test.ts     la compuerta: rompe el build ante un literal hex   <- la lección
    App.test.tsx             pruebas de renderizado del conmutador
```

## El antes

`GenericView.tsx` es la página que las reglas de diseño existen para evitar: un `<h1>` centrado de "Welcome to…", un párrafo de subtítulo, un botón con degradado de azul a morado, y alrededor de una docena de valores hex que alguien tuvo que elegir.

No está roto y no es feo. **Es genérico**: podría pertenecer a cualquier producto. Y solo funciona en modo oscuro: cambia el host de desarrollo a `data-theme="light"` y se queda tercamente oscuro, porque ninguno de sus colores pasa por un token.

## Las cuatro reglas

`BrandedView.tsx` renderiza los mismos datos bajo cuatro restricciones.

**1. Tres niveles tipográficos, siempre.** Una etiqueta eyebrow, luego un `<h1>` de verdad, luego el texto de apoyo en `var(--color-text-secondary)`. Nunca empieces con un párrafo; nunca uses el mismo peso para todo.

```tsx
<p className="hz-eyebrow">USA · 2025</p>
<h1>Macro snapshot</h1>
<p style={{ color: "var(--color-text-secondary)" }}>{SAMPLE.summary}</p>
```

**2. El acento aparece una vez por pantalla.** `--color-accent` marca aquello que quieres que se pulse: aquí, un único `hz-btn--primary`. Dos acentos es ningún acento. Los colores de estado (`--color-success`, `--color-warning`, `--color-error`) son para *estado*, no decoración, y no cuentan contra el presupuesto.

**3. Los fondos van por capas, y la tarjeta es dueña de su superficie.** `--color-bg-primary` (página) va debajo de `--color-bg-elevated` (tarjetas). `hz-card` ya trae la superficie, el radio y la sombra, así que no escribes ninguno. Una segunda sombra hecha a mano es cómo una página deja de parecerse al resto de Hub.

**4. El espaciado sale de la escala.** `var(--space-*)` es una escala de 4px. Las secciones principales llevan `--space-12` o más. El espacio en blanco generoso gana a un diseño denso; el espacio vacío es parte del diseño.

Fíjate también en que el modificador de estado se elige **a partir de los datos**, no por gusto:

```tsx
const direction = trend(SAMPLE.delta_pct);   // determinista, en sample.ts
className={direction === "improving" ? "hz-stat__number--success" : "hz-stat__number--warning"}
```

Esa es la misma disciplina que en un pack: lo determinista decide, y la presentación obedece.

## Por qué los tokens sobreviven a la marca blanca

Esta es la parte que conviene entender en vez de memorizar. El SDK publica sus tokens dentro de una **capa de cascada de CSS**:

```css
@layer huitzo-tokens {
  :root { --color-accent: …; --space-4: …; }
}
```

Cualquier cosa que un host defina *fuera de una capa* gana sobre una regla en capa **sin importar el orden de las hojas de estilo**. Así que cuando tu dashboard corre en `/d/{slug}` dentro de un Hub de marca blanca, los tokens de marca sin capa de ese Hub ganan automáticamente, y tu dashboard se reestiliza sin cambiar una línea. Corre el mismo bundle de forma independiente y cae de vuelta a los valores por defecto del SDK.

Las primitivas `hz-*` están deliberadamente *fuera* de la capa: solo consumen `var(--color-*)`, así que toman el conjunto de tokens que haya ganado.

Ese mecanismo es toda la razón por la que "nunca escribas un hex" es una regla de ingeniería real y no una preferencia estética. **Un literal hex es lo único que un host no puede sobrescribir.**

> Un detalle que conviene tener claro: los tokens resuelven en `:root`, así que están disponibles en todas partes. La clase `huitzo-dashboard` que verás en el elemento raíz (y que `TemplateFrame` añade por ti) es un gancho de alcance para CSS del host y de marca blanca; *no* es lo que hace que los tokens resuelvan.

## Las reglas como prueba, no como documento

Una guía de estilo que nadie ejecuta es una guía de estilo que nadie sigue. `design-rules.test.ts` lee el código de la vista con marca y falla ante los errores que importan:

```ts
it("contains no hex colour literals", () => {
  expect(BRANDED.match(HEX) ?? []).toEqual([]);
});

it("spends the accent exactly once", () => {
  const accents = BRANDED.match(/hz-btn--primary|hz-eyebrow--accent|hz-card--accent/g) ?? [];
  expect(accents).toHaveLength(1);
});
```

Nueve comprobaciones en total: sin hex, sin `rgb()`/`hsl()`, sin sombras escritas a mano, sin kit de UI ni librería de animación, un acento, espaciado en la escala y jerarquía de tres niveles. Dos más verifican que `GenericView` siga siendo un *mal* ejemplo, para que la comparación no se pudra en silencio cuando alguien lo ordene.

Una sutileza que la implementación tuvo que resolver: **quita los comentarios antes de escanear.** Estos archivos explican las reglas en prosa, así que un escaneo sin limpiar cuenta la frase "usa `hz-btn--primary`" como un uso del acento. Un linter que lee su propia documentación como código es un linter que grita en falso.

Apúntalo al `src/` de tu propio dashboard y funciona sin cambios. Si falla, el arreglo nunca es borrar la comprobación: busca el color que querías en el conjunto de tokens y usa su `var(--color-*)`.

## Verifica ambos temas antes de darlo por hecho

1. `npm run dev` y míralo en oscuro.
2. Abre `index.html`, cambia `data-theme="dark"` por `"light"`, recarga.
3. Ambos deben verse intencionales.

Si el claro se ve deslavado o algo desaparece, tienes un color fijo filtrándose en alguna parte, y la prueba de arriba te dirá en qué archivo.

## Para ir más lejos: primitivas para copiar

Cuando falte una primitiva, no la reinventes localmente. [`@huitzo/dashboard-primitives`](https://www.npmjs.com/package/@huitzo/dashboard-primitives) es un registro para copiar, estilo shadcn: código React tipado por primitiva, estilizado con tokens de marca y fijado por hash SHA-256, así que el código es tuyo pero sigue coincidiendo con Hub.

## Siguiente

Ya sabes hacer que un dashboard se vea bien. Los peldaños restantes cubren formularios declarativos, comandos en streaming y encolados, y la interfaz gobernada que renderiza una decisión retenida y su registro de evidencia; consulta [la ruta de aprendizaje](../../docs/es/index.md#la-ruta-de-dashboards). El peldaño final que ambas rutas comparten es [`06-fullstack-triage`](../06-fullstack-triage).
