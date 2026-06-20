"""Tests for the daily-digest command. Python owns every number; the model only narrates."""

from __future__ import annotations

import pytest

from daily_digest.commands.daily_digest import daily_digest
from daily_digest.models.args import DigestArgs
from daily_digest.models.output import DailyDigest, DigestNarrative

# A multi-day series for Tide Mart. Five steady days near 100, then one day that
# clearly spikes. The spike is obvious to a human and must be caught by Python.
_SPIKING_CSV = """date,category,amount
2026-06-01,snacks,60
2026-06-01,drinks,40
2026-06-02,snacks,55
2026-06-02,drinks,45
2026-06-03,snacks,62
2026-06-03,drinks,38
2026-06-04,snacks,58
2026-06-04,drinks,44
2026-06-05,snacks,61
2026-06-05,drinks,41
2026-06-06,snacks,260
2026-06-06,drinks,180
"""

# A flat series: every day lands at 100. Nothing should be flagged.
_FLAT_CSV = """date,category,amount
2026-06-01,snacks,60
2026-06-01,drinks,40
2026-06-02,snacks,60
2026-06-02,drinks,40
2026-06-03,snacks,60
2026-06-03,drinks,40
2026-06-04,snacks,60
2026-06-04,drinks,40
2026-06-05,snacks,60
2026-06-05,drinks,40
"""

# A clean series with two malformed rows mixed in: a non-numeric amount and a row
# missing its category. Both should be skipped and counted, with no crash.
_MALFORMED_CSV = """date,category,amount
2026-06-01,snacks,60
2026-06-01,drinks,not-a-number
2026-06-02,snacks,55
2026-06-02,,45
2026-06-03,snacks,62
"""


@pytest.mark.asyncio
async def test_spiking_day_is_flagged_by_python(mock_ctx):
    mock_ctx.llm.complete.return_value = DigestNarrative(summary="A busy day at Tide Mart.")

    result = await daily_digest(DigestArgs(sales_csv=_SPIKING_CSV), mock_ctx)

    assert isinstance(result, DailyDigest)
    # Totals and top category are deterministic.
    assert result.total_sales == 944.0
    assert result.top_category == "snacks"
    assert result.day_count == 6
    assert result.rows_skipped == 0
    # Python -- not the model -- flags the spiking day.
    flagged_dates = {a.date for a in result.anomalies}
    assert "2026-06-06" in flagged_dates


@pytest.mark.asyncio
async def test_flat_series_has_no_anomalies(mock_ctx):
    mock_ctx.llm.complete.return_value = DigestNarrative(summary="A steady day at Tide Mart.")

    result = await daily_digest(DigestArgs(sales_csv=_FLAT_CSV), mock_ctx)

    assert result.anomalies == []
    assert result.total_sales == 500.0
    assert result.day_count == 5


@pytest.mark.asyncio
async def test_malformed_rows_are_skipped_and_counted(mock_ctx):
    mock_ctx.llm.complete.return_value = DigestNarrative(summary="A quiet day at Tide Mart.")

    result = await daily_digest(DigestArgs(sales_csv=_MALFORMED_CSV), mock_ctx)

    # Two bad rows: one non-numeric amount, one missing category.
    assert result.rows_skipped == 2
    # Only the three valid rows count toward the total.
    assert result.total_sales == 177.0


@pytest.mark.asyncio
async def test_calls_a_profile_and_grounds_the_prompt_on_the_total(mock_ctx):
    mock_ctx.llm.complete.return_value = DigestNarrative(summary="A busy day at Tide Mart.")

    await daily_digest(DigestArgs(sales_csv=_SPIKING_CSV), mock_ctx)

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is DigestNarrative  # structured output
    assert "model" not in call.kwargs  # a pack must never name a model
    # Grounding: the computed total is handed to the model, not asked of it.
    assert "944.0" in call.kwargs["prompt"]
