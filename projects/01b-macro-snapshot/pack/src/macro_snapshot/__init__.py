"""macro_snapshot: a Tier 1 Intelligence Pack.

Pulls one macro indicator for one country from the World Bank API, computes the
latest observation and its delta in deterministic Python, and asks the model to
narrate only those numbers. The HTTP integration is swappable: point it at any
internal API and the same pattern holds.
"""
