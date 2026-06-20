// A tiny mock of the Huitzo Hub API, so the dashboard runs locally with no Hub.
// Run it with `node mock-server.mjs` in one terminal and `npm run dev` in another;
// dev.tsx points apiUrl at http://localhost:8787, so every command call lands here.
// It answers the provider's initial user/packs fetch and the country-snapshot call.

import { createServer } from "node:http";

const snapshot = {
  country: "USA",
  indicator: "inflation",
  latest_value: 3.4,
  latest_year: "2025",
  delta_pct: -0.6,
  summary: "Inflation eased over the latest period, down from the prior year.",
};

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

  if (req.method === "OPTIONS") {
    res.writeHead(204, cors);
    res.end();
    return;
  }
  if (req.method === "GET" && (url.includes("/auth/me") || url.includes("/users/me"))) {
    return send(200, {
      data: {
        id: "usr_dev",
        email: "dev@reef.example",
        name: "Dev",
        role: "owner",
        developerMode: true,
        tenantSlug: "reef",
        createdAt: "2026-01-01T00:00:00Z",
      },
    });
  }
  if (req.method === "GET" && url.includes("/packs")) {
    return send(200, {
      data: { packs: [{ id: "reef-macro-snapshot", name: "macro-snapshot", namespace: "reef", version: "0.1.0" }] },
    });
  }
  if (req.method === "POST" && url.includes("/commands")) {
    return send(200, { data: { result: snapshot, execution: { duration_ms: 7, status: "completed" } } });
  }
  send(200, { data: {} });
});

server.listen(8787, () => console.log("mock Hub API on http://localhost:8787"));
