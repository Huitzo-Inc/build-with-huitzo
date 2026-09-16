// The content both views render. It is the CountrySnapshot shape you already met
// in D1 (`@reef/macro-snapshot/country-snapshot`), frozen as a fixed sample.
//
// This rung is about design, so it makes no command call. Same data, two
// treatments — that is the entire experiment, and holding the data still is what
// makes the comparison honest.

export interface CountrySnapshot {
  country: string;
  indicator: string;
  latest_value: number;
  latest_year: string;
  delta_pct: number;
  summary: string;
}

export const SAMPLE: CountrySnapshot = {
  country: "USA",
  indicator: "inflation",
  latest_value: 3.4,
  latest_year: "2025",
  delta_pct: -0.6,
  summary:
    "Inflation eased over the latest period, down from the prior year. The deterministic comparison ran in Python; this sentence is the only part a model wrote.",
};

/** Deterministic, so both views agree on what "good" looks like. */
export function trend(deltaPct: number): "improving" | "worsening" | "flat" {
  if (deltaPct < 0) return "improving";
  if (deltaPct > 0) return "worsening";
  return "flat";
}
