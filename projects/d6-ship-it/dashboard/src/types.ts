// The contract with the pack, and the only thing this dashboard shares with it.
//
// `COMMAND` is the id the preflight cross-checks against huitzo-dashboard.yaml:
// if you call a command whose pack is not declared in pack_dependencies, Hub has
// no idea your dashboard needs it. That mismatch is invisible until you publish,
// which is exactly the class of mistake this rung is about catching earlier.
//
// The types mirror grounded_reco/models/output.py. No code is shared; the two
// sides agree on a command id and a shape.

export const COMMAND = "@reef/grounded-reco/recommend";

export interface Candidate {
  name: string;
  cost: number;
  quality: number;
  reliability: number;
  as_of: string;
}

export interface ScoredCandidate {
  name: string;
  score: number;
  as_of: string;
}

export interface AuditRecord {
  timestamp: string;
  autonomy: "suggest";
  candidate_count: number;
  pick: string | null;
  eval_passed: boolean;
  eval_findings: string[];
  escalated: boolean;
}

export interface Recommendation {
  pick: string | null;
  score: number | null;
  ranked: ScoredCandidate[];
  justification: string | null;
  eval_passed: boolean;
  eval_findings: string[];
  withheld: boolean;
  escalated: boolean;
  audit: AuditRecord;
}
