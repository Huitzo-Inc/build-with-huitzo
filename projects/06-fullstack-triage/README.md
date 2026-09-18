# Tier 6: fullstack-triage

> Read this in [Español](./README.es.md).

This is where the two halves meet. Tide Mart wants to triage employee expenses: list them, classify each one, and approve or reject it. You build the whole thing as one Huitzo project: an Intelligence Pack with three commands, and a React dashboard that drives them, living side by side and tested end to end on your laptop.

The one idea to carry out of here: **the pack and the dashboard are two artifacts coupled by exactly one thing, the command API.** The pack owns the decisions in deterministic Python; the dashboard renders them and sends back the human's choices. They share no code. They agree on three command ids and the shape of what flows across.

**You will learn:** how a pack and a dashboard live in one project, how the dashboard reads with `useCommand` and writes with `client.commands.execute`, the optimistic-update-with-revert pattern for a responsive UI, and how to run the whole stack locally before any Hub exists.

**Time:** about an hour.

## One project, two artifacts

A fullstack Huitzo project is scaffolded by `huitzo project init expense-triage --with-dashboard`. It is not a third kind of thing with its own manifest; it is just a `pack/` and a `dashboard/` in one directory, each with the manifest it already had.

```
06-fullstack-triage/
  pack/                          the Intelligence Pack (Python)
    huitzo.yaml                  three commands: list, classify, approve
    src/expense_triage/
      commands/list_expenses.py      deterministic, no model
      commands/classify_expense.py   rules first, model only for the fuzzy ones
      commands/approve_expense.py     records a human's decision, no model
      rules.py                       the vendor table + the approval threshold
      models/                        typed args and output (mirrored in the dashboard)
    tests/                       10 offline tests
  dashboard/                     the React frontend (TypeScript)
    huitzo-dashboard.yaml        depends on @reef/expense-triage
    src/
      components/ExpensePanel.tsx    wires the SDK: useCommand + client.commands.execute
      components/ExpenseTable.tsx    holds the optimistic-update logic (SDK-free)
      components/ExpenseRow.tsx      pure presentation
      types.ts                       the command ids + the mirrored result types
    *.test.tsx                   7 offline tests
```

## Run it

The two halves are independent, so you test them independently.

```bash
# The pack
cd pack
pip install -e ".[dev]"
pytest -q            # 10 passing tests

# The dashboard
cd ../dashboard
npm install
npm test             # 7 passing tests
npm run build        # bundles dist/main.js (exports mount/unmount)
```

## The pack: rules first, model for the fuzzy 10%

`classify-expense` is the pattern to study. The deterministic rules run first and place the common vendors with no model call. Only a vendor the table cannot match reaches the model:

```python
category = rules.classify_by_rules(args.vendor)
if category is not None:
    return ClassifyResult(..., source="rules")   # the 90%: no tokens spent

classification = await ctx.llm.complete(..., schema=Classification)  # the fuzzy 10%
return ClassifyResult(..., category=classification.category, source="model")
```

The test asserts this directly: a known vendor (`Uber`) classifies through the rules and the model is never called. `needs_approval` is always Python's, a fixed dollar threshold, never the model's. And `approve-expense` only records the decision a human made in the dashboard; the pack is `suggest` autonomy and never approves on its own.

## The dashboard: read with a hook, write with the client

The dashboard reads and writes through two different SDK surfaces, on purpose
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

### `execute()` returns a union, so narrow it

`client.commands.execute()` does not always hand you a result. A **fast**-queue
command runs inline and returns `CommandResult<T>` (HTTP 200). A **medium** or
**long**-queue command is handed to a worker and returns a `CommandReceipt`
(HTTP 202): a `task_id` to poll, *not* the output. The SDK makes that explicit in
the type, so the compiler forces you to decide which you are dealing with:

```tsx
const res = await client.commands.execute<ClassifyResult>(CLASSIFY_EXPENSE, {...});
if (isCommandReceipt(res)) {
  throw new Error(`queued as ${res.task_id}; poll client.tasks.get() for the result`);
}
return res.result.category;   // narrowed to CommandResult<ClassifyResult>
```

`classify-expense` is a fast command, so the receipt branch means the deployment
was misconfigured. Import the `isCommandReceipt` guard from `@huitzo/dashboard-sdk`
(the core package), not from the React one.

## Optimistic updates, with revert

When a user clicks Approve, the row should flip instantly, not wait for a round trip. `ExpenseTable` flips the status optimistically, then calls the command; if the command fails, it puts the old state back and shows the error:

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

Because `ExpenseTable` takes plain async callbacks instead of calling the SDK itself, this logic is tested with no Hub: one test passes a callback that resolves and asserts the change sticks, another passes one that rejects and asserts the row reverts.

## The contract: no shared code

The pack and the dashboard never import each other. `pack/src/expense_triage/models/output.py` defines `Expense` in Pydantic; `dashboard/src/types.ts` mirrors it in TypeScript; both agree on the three command ids. That single, narrow contract is the entire coupling. Change the pack's internal logic freely; as long as the commands keep their shape, the dashboard does not care.

## Test the whole thing on your laptop

Two ways, both Hub-free:

- **Fast loop:** `node mock-server.mjs` in one terminal, `npm run dev` in another. `dev.tsx` points `apiUrl` at the mock server, which answers all three commands. The full UI works in the browser.
- **Real round trip:** run the actual pack locally with `huitzo pack dev`, then point `dev.tsx`'s `apiUrl` at that local pack server instead of the mock. Now `useCommand` and `client.commands.execute` call the real Python commands you wrote, pack to dashboard, with zero cloud Hub.

## Publish independently

The pack and the dashboard version and ship on their own:

```bash
cd pack && huitzo pack publish
cd ../dashboard && huitzo dashboard build && huitzo dashboard publish
```

Coordinate a release with a single git tag at the project root. The command API is the contract between them, so as long as it holds, each can ship on its own cadence.

## Next

You have built every layer: a pack, a governed pipeline, a frontend, the four outside-in doors, and now a fullstack project. The capstone, `07-sovereign-suite`, composes all of it into a multi-tenant, deploy-anywhere governed system. It is specced and tracked, and coming next.
