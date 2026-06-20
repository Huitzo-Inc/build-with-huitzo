// The DEV-ONLY entry point, and the trick that lets a dashboard run with no Hub.
//
// In production, Hub builds the HuitzoContext and calls mount(). Here we build a
// mock context by hand and call mount() ourselves. `huitzo dashboard dev` (or
// `npm run dev`) serves index.html, which loads this file. Point `apiUrl` at a
// small local mock server that returns a canned country-snapshot response, and the
// whole dashboard runs against it with zero cloud Hub. See the README.

import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { mount } from "./main";

const devContext: HuitzoContext = {
  apiUrl: "http://localhost:8787", // point this at your local mock server
  getToken: () => "dev-token",
  slug: "first-dashboard",
  sdkVersion: "dev",
  user: {
    id: "usr_dev",
    email: "dev@reef.example",
    name: "Dev",
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
