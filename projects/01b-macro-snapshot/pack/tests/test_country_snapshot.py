"""Tests for the country-snapshot command.

Every test is offline. The HTTP response is mocked into the shape the World Bank
actually returns, and the model call is mocked to a validated MacroSummary. The
point of the suite is to prove the numbers come from Python, not the model.
"""

from __future__ import annotations

import json

import pytest
from huitzo_sdk.errors import ExternalAPIError

from macro_snapshot.commands.country_snapshot import country_snapshot
from macro_snapshot.models.args import SnapshotArgs
from macro_snapshot.models.output import CountrySnapshot, MacroSummary


def _wb_payload(observations: list[dict | None]) -> list:
    """Build a realistic two-element World Bank payload: [metadata, observations]."""
    return [
        {"page": 1, "pages": 1, "per_page": 5, "total": len(observations)},
        observations,
    ]


# Newest-first, the way the World Bank returns it. 2024 has a gap (null value)
# on purpose so the test proves we skip nulls and still pick a real latest.
_WB_OK = _wb_payload(
    [
        {"date": "2024", "value": None, "country": {"value": "United States"}},
        {"date": "2023", "value": 27_360_000_000_000.0, "country": {"value": "United States"}},
        {"date": "2022", "value": 25_744_000_000_000.0, "country": {"value": "United States"}},
        {"date": "2021", "value": 23_315_000_000_000.0, "country": {"value": "United States"}},
        {"date": "2020", "value": 21_060_000_000_000.0, "country": {"value": "United States"}},
    ]
)


@pytest.mark.asyncio
async def test_picks_latest_non_null_and_computes_delta(mock_ctx):
    mock_ctx.http.get.return_value = _WB_OK
    mock_ctx.llm.complete.return_value = MacroSummary(
        summary="US GDP was about 27.36 trillion dollars in 2023, up from the prior year."
    )

    result = await country_snapshot(SnapshotArgs(country="USA", indicator="gdp"), mock_ctx)

    assert isinstance(result, CountrySnapshot)
    # 2024 is null, so the latest real point is 2023, Python skips the gap.
    assert result.latest_value == 27_360_000_000_000.0
    assert result.latest_year == "2023"
    # Delta from 2022 (25.744T) to 2023 (27.36T) = +6.28% (rounded in Python).
    assert result.delta_pct == 6.28
    assert result.source == "World Bank"
    assert result.country == "USA"
    assert result.indicator == "gdp"


@pytest.mark.asyncio
async def test_accepts_json_string_response(mock_ctx):
    # The integration may return a JSON string instead of a parsed dict/list.
    mock_ctx.http.get.return_value = json.dumps(_WB_OK)
    mock_ctx.llm.complete.return_value = MacroSummary(summary="x")

    result = await country_snapshot(SnapshotArgs(country="USA"), mock_ctx)

    assert result.latest_value == 27_360_000_000_000.0
    assert result.latest_year == "2023"


@pytest.mark.asyncio
async def test_no_data_is_handled_gracefully(mock_ctx):
    # All observations null / empty: no crash, numeric fields are None.
    mock_ctx.http.get.return_value = _wb_payload(
        [
            {"date": "2024", "value": None},
            {"date": "2023", "value": None},
        ]
    )
    mock_ctx.llm.complete.return_value = MacroSummary(
        summary="No recent data is available for this indicator."
    )

    result = await country_snapshot(SnapshotArgs(country="PER", indicator="inflation"), mock_ctx)

    assert result.latest_value is None
    assert result.latest_year is None
    assert result.delta_pct is None


@pytest.mark.asyncio
async def test_single_point_has_no_delta(mock_ctx):
    mock_ctx.http.get.return_value = _wb_payload([{"date": "2023", "value": 100.0}])
    mock_ctx.llm.complete.return_value = MacroSummary(summary="One data point only.")

    result = await country_snapshot(SnapshotArgs(country="CHL"), mock_ctx)

    assert result.latest_value == 100.0
    assert result.latest_year == "2023"
    assert result.delta_pct is None


@pytest.mark.asyncio
async def test_calls_http_with_mapped_indicator_code_and_mrv(mock_ctx):
    mock_ctx.http.get.return_value = _WB_OK
    mock_ctx.llm.complete.return_value = MacroSummary(summary="x")

    await country_snapshot(SnapshotArgs(country="COL", indicator="inflation"), mock_ctx)

    mock_ctx.http.get.assert_awaited_once()
    call = mock_ctx.http.get.await_args
    # Friendly name "inflation" maps to the World Bank code in Python, not the model.
    assert call.args[0] == "/v2/country/COL/indicator/FP.CPI.TOTL.ZG"
    assert call.kwargs["params"]["format"] == "json"
    assert call.kwargs["params"]["mrv"] == 5


@pytest.mark.asyncio
async def test_calls_a_profile_never_a_model_and_grounds_the_prompt(mock_ctx):
    mock_ctx.http.get.return_value = _WB_OK
    mock_ctx.llm.complete.return_value = MacroSummary(summary="x")

    await country_snapshot(SnapshotArgs(country="USA", indicator="gdp"), mock_ctx)

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is MacroSummary  # structured output
    assert "model" not in call.kwargs  # a pack must never name a model
    # Grounding: the figure Python computed is in the prompt the model sees.
    prompt = call.kwargs["prompt"]
    assert "27360000000000" in prompt.replace("_", "") or "27360000000000.0" in prompt
    assert "2023" in prompt


@pytest.mark.asyncio
async def test_unexpected_shape_raises_external_api_error(mock_ctx):
    # A bare dict is not the two-element World Bank list, fail loudly and clearly.
    mock_ctx.http.get.return_value = {"unexpected": "shape"}

    with pytest.raises(ExternalAPIError):
        await country_snapshot(SnapshotArgs(country="USA"), mock_ctx)


@pytest.mark.asyncio
async def test_observations_not_a_list_raises_external_api_error(mock_ctx):
    # Right outer shape, wrong inner shape: observations should be a list.
    mock_ctx.http.get.return_value = [{"page": 1}, {"not": "a list"}]

    with pytest.raises(ExternalAPIError):
        await country_snapshot(SnapshotArgs(country="MEX"), mock_ctx)
