// Dev entry: build a mock Hub context and mount the app, so the dashboard runs with
// no Hub. Point apiUrl at mock-server.mjs (or at a local `huitzo pack dev` server, see
// the README) and the list/classify/approve commands round-trip on your laptop.

import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { mount } from "./main";

const devContext: HuitzoContext = {
  apiUrl: "http://localhost:8787",
  getToken: () => "dev-token",
  slug: "expense-triage",
  sdkVersion: "dev",
  user: {
    id: "usr_dev",
    email: "dana@reef.example",
    name: "Dana",
    roles: ["owner"],
    tenantId: "ten_dev",
  },
  navigate: (path) => console.log("navigate ->", path),
  navigateToHub: () => alert("← Hub (mock)"),
  navigateToDashboard: (slug) => console.log("dashboard ->", slug),
  showNotification: (message, type) => console.log(`[${type}] ${message}`),
  on: () => () => {},
  emit: () => {},
};

const container = document.getElementById("root");
if (container) {
  mount(container, devContext);
}
