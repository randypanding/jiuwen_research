from __future__ import annotations

from swarmdev.contracts import CapabilityToken, HoldoutScenario, OracleBundle


class HoldoutStore:
    def __init__(self, bundle: OracleBundle):
        self.bundle = bundle
        self._epoch = max((s.rotation_epoch for s in bundle.scenarios), default=0)

    def get(
        self, token: CapabilityToken, scenario_ids: list[str] | None = None
    ) -> list[HoldoutScenario]:
        # PDR-001 §7：holdout 判据对 builder/leader 不可见，读取必须持能力令牌
        token.require("holdout.read")
        if scenario_ids is None:
            return list(self.bundle.scenarios)
        wanted = set(scenario_ids)
        return [s for s in self.bundle.scenarios if s.scenario_id in wanted]

    def rotate(
        self, token: CapabilityToken, new_scenarios: list[HoldoutScenario], epoch: int
    ) -> None:
        token.require("holdout.write")
        if epoch <= self._epoch:
            raise ValueError(f"rotation epoch must increase: {epoch} <= {self._epoch}")
        self.bundle.scenarios = [
            s.model_copy(update={"rotation_epoch": epoch}) for s in new_scenarios
        ]
        self._epoch = epoch
