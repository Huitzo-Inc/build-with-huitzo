"""
Module: expense_triage.rules
Description: The deterministic core, kept apart from the commands. A vendor-keyword
            table classifies the common cases, and a fixed dollar threshold decides
            what needs approval. The model is only ever consulted when this table
            cannot place a vendor, which in practice is the small minority of cases.
"""

from __future__ import annotations

from expense_triage.models.output import Category, Expense

# Vendor keyword -> category. This table handles the common, unambiguous cases with
# zero tokens spent. Extend it as you learn your real vendors.
_VENDOR_RULES: dict[str, Category] = {
    "uber": "travel",
    "lyft": "travel",
    "delta": "travel",
    "airbnb": "travel",
    "marriott": "travel",
    "restaurant": "meals",
    "cafe": "meals",
    "coffee": "meals",
    "doordash": "meals",
    "github": "software",
    "figma": "software",
    "aws": "software",
    "notion": "software",
    "staples": "office",
    "office depot": "office",
}

# Expenses at or above this need a human approval before they are reimbursed.
_APPROVAL_THRESHOLD = 500.0


def classify_by_rules(vendor: str) -> Category | None:
    """Return a category if a vendor keyword matches, else None (the model decides)."""
    haystack = vendor.lower()
    for keyword, category in _VENDOR_RULES.items():
        if keyword in haystack:
            return category
    return None


def needs_approval(amount: float) -> bool:
    """A fixed, auditable threshold. No model decides what needs a human's sign-off."""
    return amount >= _APPROVAL_THRESHOLD


# A small seeded set so list-expenses returns something without a database. In a real
# pack this would come from ctx.storage or ctx.db.
SEED_EXPENSES: list[Expense] = [
    Expense(id="E-1", vendor="Uber", amount=42.50, memo="airport ride", category="travel", status="pending"),
    Expense(id="E-2", vendor="Blue Bottle Coffee", amount=18.00, memo="team coffee", category="meals", status="approved"),
    Expense(id="E-3", vendor="GitHub", amount=21.00, memo="seat", category="software", status="pending"),
    Expense(id="E-4", vendor="Highwater Consulting", amount=1200.00, memo="advisory retainer", category=None, status="pending"),
]
