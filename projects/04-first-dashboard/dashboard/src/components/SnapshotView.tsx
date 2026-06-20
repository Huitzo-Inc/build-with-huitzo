// The presentational layer. It takes plain props and renders the four states a
// command call can be in: idle, loading, error, success. It calls no hooks and
// imports no SDK, which is exactly why it is trivial to unit-test (see
// SnapshotView.test.tsx). The container (SnapshotPanel) wires the real useCommand
// to these props.

import {
  COUNTRIES,
  INDICATORS,
  formatDelta,
  formatValue,
  type CountrySnapshot,
  type Indicator,
} from "../types";

export interface SnapshotViewProps {
  country: string;
  indicator: Indicator;
  onCountry: (country: string) => void;
  onIndicator: (indicator: Indicator) => void;
  onRun: () => void;
  loading: boolean;
  error: Error | null;
  data: CountrySnapshot | null;
}

export function SnapshotView(props: SnapshotViewProps) {
  const { country, indicator, onCountry, onIndicator, onRun, loading, error, data } = props;

  return (
    <section className="hz-card hz-card--lg" aria-label="Macro snapshot">
      <p className="hz-eyebrow hz-eyebrow--accent">Macro snapshot</p>

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "flex-end" }}>
        <label>
          Country{" "}
          <select value={country} onChange={(e) => onCountry(e.target.value)} aria-label="Country">
            {COUNTRIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Indicator{" "}
          <select
            value={indicator}
            onChange={(e) => onIndicator(e.target.value as Indicator)}
            aria-label="Indicator"
          >
            {INDICATORS.map((i) => (
              <option key={i.value} value={i.value}>
                {i.label}
              </option>
            ))}
          </select>
        </label>

        <button className="hz-btn hz-btn--primary" onClick={onRun} disabled={loading}>
          {loading ? "Running..." : "Run snapshot"}
        </button>
      </div>

      {loading && <p role="status">Asking the pack...</p>}

      {error && (
        <p className="hz-card--warning" role="alert">
          {error.message}
        </p>
      )}

      {data && !loading && (
        <div>
          <p className="hz-stat__number">{formatValue(data.latest_value)}</p>
          <p>
            {data.indicator} for {data.country}
            {data.latest_year ? `, ${data.latest_year}` : ""} ({formatDelta(data.delta_pct)} vs prior)
          </p>
          <p>{data.summary}</p>
        </div>
      )}
    </section>
  );
}
