from __future__ import annotations

from swarm_kernel.contracts.fanout import (
    MeasurementClassification,
    MeasurementEvent,
)
from swarm_kernel.contracts.oracle import ScenarioOutcome


def classify_fanout(
    fanout_id: str,
    delta_id: str,
    per_instance_pass: dict[str, bool],
    divergence_detected: bool,
    divergence_inputs: list[str] | None = None,
    stronger_tier_succeeded: bool | None = None,
) -> MeasurementEvent:
    n = len(per_instance_pass)
    pass_count = sum(1 for v in per_instance_pass.values() if v)
    fail_count = n - pass_count
    if n < 3 and fail_count > 0:
        return MeasurementEvent(
            fanout_id=fanout_id,
            delta_id=delta_id,
            n_instances=n,
            pass_count=pass_count,
            fail_count=fail_count,
            divergence_detected=divergence_detected,
            divergence_inputs=divergence_inputs or [],
            classification=MeasurementClassification.INSUFFICIENT_SAMPLES,
            stronger_tier_succeeded=stronger_tier_succeeded,
        )
    if fail_count == 0:
        if divergence_detected:
            classification = MeasurementClassification.SILENCE
        else:
            classification = MeasurementClassification.CLOSED
    elif pass_count > 0:
        classification = MeasurementClassification.DIVERGENCE
    else:
        if stronger_tier_succeeded is True:
            classification = MeasurementClassification.TIER_UPGRADE_REQUIRED
        elif stronger_tier_succeeded is False:
            classification = MeasurementClassification.SPEC_ORACLE_CONFLICT
        else:
            classification = MeasurementClassification.SPEC_ORACLE_CONFLICT
    return MeasurementEvent(
        fanout_id=fanout_id,
        delta_id=delta_id,
        n_instances=n,
        pass_count=pass_count,
        fail_count=fail_count,
        divergence_detected=divergence_detected,
        divergence_inputs=divergence_inputs or [],
        classification=classification,
        stronger_tier_succeeded=stronger_tier_succeeded,
    )
