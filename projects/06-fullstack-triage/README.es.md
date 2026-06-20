<!-- i18n-source-sha: 6d7c4d5bd5acd9a834188a110badd26eb2b645afd2e7c0e5c73a42b405e4c93b -->
<!-- Traducción revisada de README.md. No edites contenido aquí: actualiza el inglés y vuelve a generar. Ver ../../.translation/README.md. -->

# Nivel 6: fullstack-triage

> Read this in [English](./README.md).

Aquí es donde se encuentran las dos mitades. Tide Mart quiere hacer triaje de los gastos de sus empleados: listarlos, clasificar cada uno y aprobarlo o rechazarlo. Construyes todo como un solo proyecto de Huitzo: un Intelligence Pack con tres comandos y un dashboard de React que los maneja, viviendo lado a lado y probados de principio a fin en tu portátil.

La idea que hay que llevarse de aquí: **el pack y el dashboard son dos artefactos acoplados por exactamente una cosa, la API de comandos.** El pack toma las decisiones en Python determinista; el dashboard las renderiza y devuelve las elecciones de la persona. No comparten código. Acuerdan tres ids de comando y la forma de lo que fluye entre ellos.

**Aprenderás:** cómo un pack y un dashboard viven en un proyecto, cómo el dashboard lee con `useCommand` y escribe con `client.commands.execute`, el patrón de actualización optimista con reversión para una interfaz ágil, y cómo correr todo el stack localmente antes de que exista un Hub.

**Tiempo:** alrededor de una hora.

## Un proyecto, dos artefactos

Un proyecto fullstack de Huitzo se genera con `huitzo project init expense-triage --with-dashboard`. No es un tercer tipo de cosa con su propio manifiesto; es solo un `pack/` y un `dashboard/` en un directorio, cada uno con el manifiesto que ya tenía.

```
06-fullstack-triage/
  pack/                          el Intelligence Pack (Python)
    huitzo.yaml                  tres comandos: list, classify, approve
    src/expense_triage/
      commands/list_expenses.py      determinista, sin modelo
      commands/classify_expense.py   reglas primero, modelo solo para los difusos
      commands/approve_expense.py     registra la decisión de una persona, sin modelo
      rules.py                       la tabla de proveedores + el umbral de aprobación
      models/                        args y salida tipados (reflejados en el dashboard)
    tests/                       10 pruebas sin conexión
  dashboard/                     el frontend de React (TypeScript)
    huitzo-dashboard.yaml        depende de @reef/expense-triage
    src/
      components/ExpensePanel.tsx    conecta el SDK: useCommand + client.commands.execute
      components/ExpenseTable.tsx    contiene la lógica de actualización optimista (sin SDK)
      components/ExpenseRow.tsx      presentación pura
      types.ts                       los ids de comando + los tipos de resultado reflejados
    *.test.tsx                   7 pruebas sin conexión
```

## Ejecútalo

Las dos mitades son independientes, así que las pruebas por separado.

```bash
# El pack
cd pack
pip install -e ".[dev]"
pytest -q            # 10 pruebas en verde

# El dashboard
cd ../dashboard
npm install
npm test             # 7 pruebas en verde
npm run build        # empaqueta dist/main.js (exporta mount/unmount)
```

## El pack: reglas primero, modelo para el 10% difuso

`classify-expense` es el patrón a estudiar. Las reglas deterministas corren primero y colocan a los proveedores comunes sin llamar al modelo. Solo un proveedor que la tabla no puede emparejar llega al modelo:

```python
category = rules.classify_by_rules(args.vendor)
if category is not None:
    return ClassifyResult(..., source="rules")   # the 90%: no tokens spent

classification = await ctx.llm.complete(..., schema=Classification)  # the fuzzy 10%
return ClassifyResult(..., category=classification.category, source="model")
```

La prueba lo afirma directamente: un proveedor conocido (`Uber`) se clasifica por las reglas y el modelo nunca se llama. `needs_approval` siempre es de Python, un umbral fijo en dólares, nunca del modelo. Y `approve-expense` solo registra la decisión que una persona tomó en el dashboard; el pack es de autonomía `suggest` y nunca aprueba por su cuenta.

## El dashboard: lee con un hook, escribe con el cliente

El dashboard lee y escribe por dos superficies distintas del SDK, a propósito
(`src/components/ExpensePanel.tsx`):

```tsx
// READ: a declarative fetch that manages loading/error/data for you.
const { data, loading, error } = useCommand<ListResult>(LIST_EXPENSES, { initialArgs: {} });

// WRITE: the client call, because a mutation needs the promise to REJECT on failure
// so the table can revert its optimistic update.
const onApprove = async (id, approve) => {
  await client.commands.execute<ApprovalResult>(APPROVE_EXPENSE, { expense_id: id, approve, approver: user?.email });
};
```

## Actualizaciones optimistas, con reversión

Cuando una persona pulsa Approve, la fila debería cambiar al instante, no esperar un viaje de ida y vuelta. `ExpenseTable` cambia el estado de forma optimista, luego llama al comando; si el comando falla, repone el estado anterior y muestra el error:

```tsx
const snapshot = expenses;
setExpenses((list) => updateExpense(list, id, { status }));  // optimistic
try {
  await onApprove(id, approve);
} catch (e) {
  setExpenses(snapshot);                                      // revert
  setError("Could not update the expense.");
}
```

Como `ExpenseTable` recibe callbacks async simples en vez de llamar al SDK ella misma, esta lógica se prueba sin Hub: una prueba pasa un callback que se resuelve y afirma que el cambio se mantiene, otra pasa uno que se rechaza y afirma que la fila se revierte.

## El contrato: nada de código compartido

El pack y el dashboard nunca se importan entre sí. `pack/src/expense_triage/models/output.py` define `Expense` en Pydantic; `dashboard/src/types.ts` lo refleja en TypeScript; ambos acuerdan los tres ids de comando. Ese contrato único y estrecho es todo el acoplamiento. Cambia la lógica interna del pack con libertad; mientras los comandos conserven su forma, al dashboard no le importa.

## Prueba todo en tu portátil

Dos formas, ambas sin Hub:

- **Bucle rápido:** `node mock-server.mjs` en una terminal, `npm run dev` en otra. `dev.tsx` apunta `apiUrl` al servidor simulado, que responde los tres comandos. La interfaz completa funciona en el navegador.
- **Ida y vuelta real:** corre el pack de verdad localmente con `huitzo pack dev`, luego apunta el `apiUrl` de `dev.tsx` a ese servidor local del pack en vez del simulado. Ahora `useCommand` y `client.commands.execute` llaman a los comandos de Python reales que escribiste, del pack al dashboard, sin Hub en la nube.

## Publica de forma independiente

El pack y el dashboard se versionan y despliegan por su cuenta:

```bash
cd pack && huitzo pack publish
cd ../dashboard && huitzo dashboard build && huitzo dashboard publish
```

Coordina un lanzamiento con una sola etiqueta de git en la raíz del proyecto. La API de comandos es el contrato entre ellos, así que mientras se mantenga, cada uno puede desplegarse a su propio ritmo.

## Siguiente

Has construido todas las capas: un pack, un pipeline gobernado, un frontend, las cuatro puertas desde fuera, y ahora un proyecto fullstack. El capstone, `07-sovereign-suite`, compone todo en un sistema gobernado, multiinquilino y desplegable en cualquier entorno. Está especificado y en seguimiento, y viene a continuación.
