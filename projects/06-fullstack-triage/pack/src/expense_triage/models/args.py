"""
Module: expense_triage.models.args
Description: Typed input for the three commands. The SDK validates these before your
            command runs, so bad input never reaches your logic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from expense_triage.models.output import Status


class ListArgs(BaseModel):
    status: Status | None = Field(default=None, description="Optional status filter (pending/approved/rejected).")


class ClassifyArgs(BaseModel):
    expense_id: str = Field(min_length=1, description="The expense to classify.")
    vendor: str = Field(min_length=1, description="Who was paid; the rules look at this first.")
    amount: float = Field(ge=0, description="Amount in dollars; drives needs_approval.")
    memo: str = Field(default="", description="Optional note; helps the model on ambiguous vendors.")


class ApproveArgs(BaseModel):
    expense_id: str = Field(min_length=1, description="The expense being decided on.")
    approve: bool = Field(description="The human's decision: True to approve, False to reject.")
    approver: str = Field(min_length=1, description="Who is making the decision.")
