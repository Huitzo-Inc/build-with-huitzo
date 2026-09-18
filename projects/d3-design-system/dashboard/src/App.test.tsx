// Render tests for the toggle. The design rules themselves are checked by reading
// the source in design-rules.test.ts; these check the thing actually works.

import { act } from "@testing-library/react";
import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { describe, expect, it } from "vitest";

import { mount, unmount } from "./main";
import { SAMPLE, trend } from "./sample";

function makeContext(): HuitzoContext {
  return {
    apiUrl: "http://localhost:8787",
    getToken: () => "test-token",
    slug: "design-system",
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
  };
}

function render() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  act(() => mount(container, makeContext()));
  return container;
}

describe("the D3 toggle", () => {
  it("opens on the branded view", () => {
    const c = render();
    expect(c.textContent).toContain("Macro snapshot");
    expect(c.querySelector(".hz-stat__number")).not.toBeNull();
    act(() => unmount(c));
  });

  it("switches to the generic view and back", () => {
    const c = render();
    const [, generic] = Array.from(c.querySelectorAll("button"));

    act(() => (generic as HTMLButtonElement).click());
    // The generic view leads with a centred welcome headline and has no eyebrow.
    expect(c.textContent).toContain("Welcome to Macro Snapshot");
    expect(c.querySelector(".hz-stat__number")).toBeNull();

    const [branded] = Array.from(c.querySelectorAll("button"));
    act(() => (branded as HTMLButtonElement).click());
    expect(c.querySelector(".hz-stat__number")).not.toBeNull();
    act(() => unmount(c));
  });

  it("renders both views from the same sample", () => {
    const c = render();
    expect(c.textContent).toContain(String(SAMPLE.latest_value));

    const [, generic] = Array.from(c.querySelectorAll("button"));
    act(() => (generic as HTMLButtonElement).click());
    expect(c.textContent).toContain(String(SAMPLE.latest_value));
    act(() => unmount(c));
  });

  it("picks the status modifier from the data, not by taste", () => {
    // delta is negative for inflation, so the trend is an improvement.
    expect(trend(SAMPLE.delta_pct)).toBe("improving");
    const c = render();
    expect(c.querySelector(".hz-stat__number--success")).not.toBeNull();
    expect(c.querySelector(".hz-stat__number--warning")).toBeNull();
    act(() => unmount(c));
  });
});

describe("trend()", () => {
  it("is deterministic in all three directions", () => {
    expect(trend(-0.6)).toBe("improving");
    expect(trend(1.2)).toBe("worsening");
    expect(trend(0)).toBe("flat");
  });
});
