// Pure presentation: props in, markup out. No SDK, no network, so it tests with
// nothing mocked.
//
// The one thing worth copying here is that `withheld` and `escalated` are rendered
// as FIRST-CLASS STATES, not as an error. A governed pack that withholds a result
// has not failed — it has done its job, and the UI has to say so plainly rather
// than showing a blank panel or a red toast.

import type { Recommendation } from "../types";

interface Props {
  loading: boolean;
  error: string | null;
  data: Recommendation | null;
  onRun: () => void;
}

export function RecommendationView({ loading, error, data, onRun }: Props) {
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
        <button className="hz-btn hz-btn--primary" onClick={onRun} disabled={loading} type="button">
          {loading ? "Running…" : "Run recommendation"}
        </button>
      </div>

      {error ? (
        <div className="hz-card hz-card--warning" role="alert">
          <p className="hz-eyebrow" style={{ margin: 0 }}>
            Command failed
          </p>
          <p style={{ margin: 0, color: "var(--color-text-secondary)" }}>{error}</p>
        </div>
      ) : null}

      {data ? (
        <>
          {/* Governance first. If the eval withheld the result, that is the
              headline — not a footnote under a number the user should not trust. */}
          {data.withheld ? (
            <div className="hz-card hz-card--warning" role="status">
              <p className="hz-eyebrow" style={{ margin: 0 }}>
                Withheld{data.escalated ? " · escalated to a human" : ""}
              </p>
              <p style={{ margin: 0, color: "var(--color-text-secondary)" }}>
                The deterministic eval did not pass, so this is not presented as a confident
                recommendation.
              </p>
            </div>
          ) : null}

          <div className="hz-card hz-card--lg">
            <p className="hz-eyebrow" style={{ margin: 0 }}>
              Pick
            </p>
            <p className={data.withheld ? "hz-stat__number hz-stat__number--warning" : "hz-stat__number"} style={{ margin: 0 }}>
              {data.pick ?? "—"}
            </p>
            {data.justification ? (
              <p style={{ marginBottom: 0, color: "var(--color-text-secondary)" }}>
                {data.justification}
              </p>
            ) : null}
          </div>

          <div className="hz-card hz-card--md">
            <p className="hz-eyebrow" style={{ margin: 0 }}>
              Eval findings
            </p>
            <ul style={{ margin: 0, paddingLeft: "var(--space-5)", color: "var(--color-text-secondary)" }}>
              {data.eval_findings.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>

          <p style={{ margin: 0, color: "var(--color-text-muted)", fontSize: "0.9rem" }}>
            Audited {data.audit.timestamp} · autonomy {data.audit.autonomy} ·{" "}
            {data.audit.candidate_count} candidates scored
          </p>
        </>
      ) : null}
    </section>
  );
}
