"""The load-bearing test for a pipeline pack.

A pipeline is only as good as its handoffs. These tests prove, with no executor and
no live Hub, that:

  1. The `pipelines:` block in huitzo.yaml is valid and the SDK can load it.
  2. Every stage names a command that actually exists in this pack.
  3. Each stage's output type carries every field the next stage's input type needs.

If someone renames a field on a stage output and forgets the downstream input, this
fails in CI, before the pipeline is ever run for real.
"""

from __future__ import annotations

from pathlib import Path

from huitzo_sdk.manifest import load_manifest

from claims_pipeline.models.args import AssessArgs, ExtractArgs, RecommendArgs
from claims_pipeline.models.output import ExtractedClaim, RiskAssessment

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "huitzo.yaml"

# The pipeline as the code understands it: stage name -> (command, input model, output model).
# The manifest must agree with this, in this order.
EXPECTED_STAGES = [
    ("extract", "extract-claim", ExtractArgs, ExtractedClaim),
    ("assess", "assess-risk", AssessArgs, RiskAssessment),
    ("recommend", "recommend-action", RecommendArgs, None),
]


def test_manifest_loads_and_declares_the_pipeline():
    manifest = load_manifest(MANIFEST_PATH)
    assert manifest.pipelines is not None
    assert "score-claim" in manifest.pipelines.root
    pipeline = manifest.pipelines.root["score-claim"]
    assert pipeline.error_strategy == "fail_fast"
    assert [s.name for s in pipeline.stages] == [name for name, _, _, _ in EXPECTED_STAGES]


def test_every_stage_references_a_real_command():
    manifest = load_manifest(MANIFEST_PATH)
    declared = {c.name for c in manifest.commands}
    pipeline = manifest.pipelines.root["score-claim"]
    for stage in pipeline.stages:
        # Stage command form is "pack:command"; the command is the last segment.
        command_name = stage.command.split(":")[-1]
        assert command_name in declared, f"stage '{stage.name}' references unknown command '{command_name}'"


def test_manifest_stage_order_matches_the_code():
    manifest = load_manifest(MANIFEST_PATH)
    pipeline = manifest.pipelines.root["score-claim"]
    manifest_commands = [s.command.split(":")[-1] for s in pipeline.stages]
    assert manifest_commands == [cmd for _, cmd, _, _ in EXPECTED_STAGES]


def test_typed_handoff_each_output_feeds_the_next_input():
    # The contract: every field a downstream stage consumes must be produced upstream.
    handoffs = [
        (ExtractedClaim, AssessArgs),    # stage 1 output -> stage 2 input
        (RiskAssessment, RecommendArgs),  # stage 2 output -> stage 3 input
    ]
    for producer, consumer in handoffs:
        produced = set(producer.model_fields)
        consumed = set(consumer.model_fields)
        missing = consumed - produced
        assert not missing, (
            f"{consumer.__name__} needs {sorted(missing)} which {producer.__name__} does not produce"
        )
