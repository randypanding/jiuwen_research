import pytest

from swarmdev.contracts import RLevel, SpecDoc
from swarmdev.gates import GateContext


def _spec() -> SpecDoc:
    return SpecDoc(
        spec_id="SPEC-demo-0001", domain="demo", version="1.0.0", l1_intent="demo intent"
    )


@pytest.fixture()
def make_ctx(tmp_path):
    def factory(**overrides) -> GateContext:
        workspace = tmp_path / "ws"
        workspace.mkdir(exist_ok=True)
        instance_dir = workspace / "inst"
        instance_dir.mkdir(exist_ok=True)
        fields = {
            "workspace": workspace,
            "spec": _spec(),
            "instance_id": "INST-1",
            "instance_dir": instance_dir,
            "r_level": RLevel.R0,
        }
        fields.update(overrides)
        return GateContext(**fields)

    return factory
