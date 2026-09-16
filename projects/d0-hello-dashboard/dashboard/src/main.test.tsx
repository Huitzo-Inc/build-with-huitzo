// The tests for this rung test the CONTRACT, not the copy on the page: Hub calls
// mount(container, context), then later unmount(container), and both must behave.
// If you break that, no amount of pretty UI will load inside Hub.
//
// These run in jsdom with no browser, no Hub and no network.

import { act } from "@testing-library/react";
import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { describe, expect, it } from "vitest";

import { mount, unmount } from "./main";

function makeContext(overrides: Partial<HuitzoContext> = {}): HuitzoContext {
  return {
    apiUrl: "http://localhost:8787",
    getToken: () => "test-token",
    slug: "hello-dashboard",
    sdkVersion: "test",
    user: {
      id: "usr_test",
      email: "tester@reef.example",
      name: "Tester",
      roles: ["owner"],
      tenantId: "ten_test",
    },
    navigate: () => {},
    navigateToHub: () => {},
    navigateToDashboard: () => {},
    showNotification: () => {},
    on: () => () => {},
    emit: () => {},
    ...overrides,
  };
}

describe("the Hub mount contract", () => {
  it("renders into the container Hub hands it", () => {
    const container = document.createElement("div");
    act(() => mount(container, makeContext()));

    expect(container.textContent).toContain("It mounted.");
    act(() => unmount(container));
  });

  it("shows the user from the mount context, not from a fetch", () => {
    const container = document.createElement("div");
    act(() => mount(container, makeContext()));

    // Nothing was fetched: every value on screen came off the context object.
    expect(container.textContent).toContain("Tester");
    expect(container.textContent).toContain("tester@reef.example");
    act(() => unmount(container));
  });

  it("survives a context with no signed-in user", () => {
    // `user` is optional on the mount context, so Hub may simply omit it.
    const container = document.createElement("div");
    act(() => mount(container, makeContext({ user: undefined })));

    expect(container.textContent).toContain("Not signed in");
    act(() => unmount(container));
  });

  it("empties the container on unmount, so Hub can reuse the node", () => {
    const container = document.createElement("div");
    act(() => mount(container, makeContext()));
    expect(container.innerHTML).not.toBe("");

    act(() => unmount(container));
    expect(container.innerHTML).toBe("");
  });

  it("tolerates unmounting a container it never mounted", () => {
    // Hub can call unmount defensively. This must not throw.
    expect(() => unmount(document.createElement("div"))).not.toThrow();
  });
});
