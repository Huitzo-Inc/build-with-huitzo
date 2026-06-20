// The contract between this dashboard and the pack it consumes. The dashboard
// shares no code with the pack; it agrees on the command id and the result shape.
// This is the TypeScript mirror of macro-snapshot's CountrySnapshot Pydantic model.

export const COUNTRY_SNAPSHOT = "@reef/macro-snapshot/country-snapshot";

export type Indicator = "gdp" | "gdp_growth" | "inflation";

export const INDICATORS: { value: Indicator; label: string }[] = [
  { value: "inflation", label: "Inflation (annual %)" },
  { value: "gdp_growth", label: "GDP growth (annual %)" },
  { value: "gdp", label: "GDP (current US$)" },
];

export const COUNTRIES: { value: string; label: string }[] = [
  { value: "USA", label: "United States" },
  { value: "MEX", label: "Mexico" },
  { value: "BRA", label: "Brazil" },
  { value: "DEU", label: "Germany" },
];

// The exact shape macro-snapshot's country-snapshot command returns. Every number
// here was computed in deterministic Python; `summary` is the one model-written field.
export interface CountrySnapshot {
  country: string;
  indicator: string;
  latest_value: number | null;
  latest_year: string | null;
  delta_pct: number | null;
  summary: string;
}

/** Format a raw indicator value for display. Pure, so it is unit-tested directly. */
export function formatValue(value: number | null): string {
  if (value === null) return "no data";
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000_000).toLocaleString(undefined, { maximumFractionDigits: 1 })}B`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

/** Format a percentage delta with an explicit sign. Pure, unit-tested. */
export function formatDelta(delta: number | null): string {
  if (delta === null) return "no prior period";
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
}
