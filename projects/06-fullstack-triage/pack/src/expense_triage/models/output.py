"""
Module: expense_triage.models.output
Description: Output models for the three commands, plus the one model slice. As in
            every Huitzo pack, the model is responsible for the smallest possible
            piece: when the deterministic rules cannot classify an expense, the model
            picks a category, and nothing else. Status, approval thresholds, and the
            recorded decision are all Python's.

            These types are also the contract the dashboard mirrors in TypeScript.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["travel", "meals", "software", "office", "other"]
Status = Literal["pending", "approved", "rejected"]


class Expense(BaseModel):
    """One expense. `category` is null until it is classified."""

    id: str = Field(description="Stable expense id.")
    vendor: str = Field(description="Who was paid.")
    amount: float = Field(description="Amount in dollars.")
    memo: str = Field(default="", description="Free-text note from the submitter.")
    category: Category | None = Field(default=None, description="Set by classify-expense, else null.")
    status: Status = Field(default="pending", description="pending until a human approves or rejects.")


class ListResult(BaseModel):
    """Output of list-expenses."""

    expenses: list[Expense] = Field(description="The expenses, optionally filtered by status.")
    total: int = Field(description="How many expenses were returned.")


class Classification(BaseModel):
    """The model slice: handed to ``ctx.llm.complete(schema=...)`` ONLY when the
    deterministic rules cannot classify the expense. The model picks a category and
    nothing else."""

    category: Category = Field(description="The best-fit category for an expense the rules could not place.")


class ClassifyResult(BaseModel):
    """Output of classify-expense. `source` records whether the rules or the model
    decided, which is the whole teaching point: most expenses never reach the model."""

    expense_id: str = Field(description="The expense that was classified.")
    category: Category = Field(description="The chosen category.")
    needs_approval: bool = Field(description="Deterministic: True when the amount is over the threshold.")
    source: Literal["rules", "model"] = Field(description="Which path classified it: 'rules' or 'model'.")


class ApprovalResult(BaseModel):
    """Output of approve-expense: the recorded human decision. Pure Python."""

    expense_id: str = Field(description="The expense decided on.")
    status: Status = Field(description="'approved' or 'rejected', from the human's decision.")
    approver: str = Field(description="Who made the decision.")
    decided_at: str = Field(description="UTC ISO-8601 timestamp of the decision.")
