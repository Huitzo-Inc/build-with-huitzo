// A tiny mock of the Hub API so the dashboard runs locally with no Hub. It answers
// the three commands by matching the path. Run `node mock-server.mjs` alongside
// `npm run dev`. For a real round-trip against the actual pack, run the pack with
// `huitzo pack dev` instead and point dev.tsx at it (see the README).

import { createServer } from "node:http";

const expenses = [
  { id: "E-1", vendor: "Uber", amount: 42.5, memo: "airport ride", category: "travel", status: "pending" },
  { id: "E-2", vendor: "Blue Bottle Coffee", amount: 18.0, memo: "team coffee", category: "meals", status: "approved" },
  { id: "E-3", vendor: "GitHub", amount: 21.0, memo: "seat", category: "software", status: "pending" },
  { id: "E-4", vendor: "Highwater Consulting", amount: 1200.0, memo: "advisory retainer", category: null, status: "pending" },
];

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Authorization,Content-Type",
};

const server = createServer((req, res) => {
  const url = req.url ?? "";
  const send = (code, body) => {
    res.writeHead(code, { "Content-Type": "application/json", ...cors });
    res.end(JSON.stringify(body));
  };
  const ok = (result) => send(200, { data: { result, execution: { duration_ms: 5, status: "completed" } } });

  if (req.method === "OPTIONS") {
    res.writeHead(204, cors);
    res.end();
    return;
  }
  if (req.method === "GET" && (url.includes("/auth/me") || url.includes("/users/me"))) {
    return send(200, { data: { id: "usr_dev", email: "dana@reef.example", role: "owner", developerMode: true } });
  }
  if (req.method === "GET" && url.includes("/packs")) {
    return send(200, { data: { packs: [{ id: "reef-expense-triage", name: "expense-triage", namespace: "reef", version: "0.1.0" }] } });
  }
  if (req.method === "POST" && url.includes("list-expenses")) {
    return ok({ expenses, total: expenses.length });
  }
  if (req.method === "POST" && url.includes("classify-expense")) {
    return ok({ expense_id: "E-4", category: "other", needs_approval: true, source: "model" });
  }
  if (req.method === "POST" && url.includes("approve-expense")) {
    return ok({ expense_id: "E-1", status: "approved", approver: "dana@reef.example", decided_at: new Date().toISOString() });
  }
  send(200, { data: {} });
});

server.listen(8787, () => console.log("mock Hub API on http://localhost:8787"));
