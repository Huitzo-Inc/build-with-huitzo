// The DEV-ONLY entry point, and the reason this whole track runs offline.
//
// In production, Hub builds the HuitzoContext and calls mount(). Here we build one
// by hand and call mount() ourselves. `npm run dev` serves index.html, which loads
// this file. That is the entire trick: a Huitzo Dashboard is just a module with a
// known entry point, so anything that can supply a context can run it.
//
// This rung makes no command call, so there is nothing for `apiUrl` to talk to
// yet — it is here because the type requires it. Rung D1 points it at a mock Hub
// and the same file starts returning real pack results.

import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { mount } from "./main";

const devContext: HuitzoContext = {
  apiUrl: "http://localhost:8787",
  getToken: () => "dev-token",
  slug: "hello-dashboard",
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
