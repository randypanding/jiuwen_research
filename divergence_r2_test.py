"""Supplementary objective test: R2 fan-out behavior across all 7 branches.

Extends divergence_test.py which only covered R3 fan-out and soft-gate abstention.
Here we check whether each implementation permits fan-out > 1 for R2 artifacts.
"""
import sys

def section(title):
    print("\n" + "=" * 70)
    print("## " + title)
    print("=" * 70)

def test_qw1_r2():
    section("QW1 (swarm-kernel) - R2 fan-out")
    sys.path.insert(0, "/tmp/checkouts/QW1/swarm-kernel")
    try:
        from swarm_kernel.contracts.fanout import FanoutRequest
        from swarm_kernel.contracts.base import RLevel
        for r in (RLevel.R0, RLevel.R1, RLevel.R2, RLevel.R3):
            try:
                fr = FanoutRequest(wave_id="W-1", delta_id="D-1", r_level=r, n_instances=3)
                print(f"  {r.value} n_instances=3 -> ACCEPTED")
            except Exception as e:
                print(f"  {r.value} n_instances=3 -> REJECTED: {type(e).__name__}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_qw3_r2_policy():
    section("QW3 (opc) - R2/R3 fan-out at ADMISSION policy layer")
    sys.path.insert(0, "/tmp/checkouts/QW3/opc/src")
    try:
        from opc.schemas.wave import WaveManifest
        from opc.schemas.common import RLevel
        from opc.world.ledger import AdmissionLedger
        from opc.world.admission import AdmissionController
        import tempfile, os
        led = AdmissionLedger(path=tempfile.mkdtemp())
        ctrl = AdmissionController(led)
        for r in (RLevel.R0, RLevel.R1, RLevel.R2, RLevel.R3):
            m = WaveManifest(wave_id=f"WAVE-{r.value}", spec_version="1", fanout_n=3, r_levels={"A": r})
            ctrl.begin_wave(m)
            v = ctrl.fanout_policy_violation(f"WAVE-{r.value}", "A", 3)
            print(f"  WaveManifest fanout_n=3, r={r.value} -> policy_violation={v!r}")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_qw2_r3_min3():
    section("QW2 (swarmfoundry) - does code enforce D-20 'R3 forces N>=3'?")
    sys.path.insert(0, "/tmp/checkouts/QW2/swarmfoundry/src")
    try:
        from swarmfoundry.schema.wave import WaveTask
        for n in (1, 3, 8):
            try:
                t = WaveTask.from_dict({"task_id": "T-1", "spec_delta_id": "D-1", "r_level": "R3", "n_fanout": n}, "test")
                print(f"  R3 n_fanout={n} -> ACCEPTED (D-20 says R3 must be >=3, but schema accepts any 1..8)")
            except Exception as e:
                print(f"  R3 n_fanout={n} -> REJECTED: {type(e).__name__}: {e}")
        # check if a fanout decision function exists that enforces N>=3 for R3
        import pkgutil, swarmfoundry
        mods = [m.name for m in pkgutil.iter_modules(swarmfoundry.__path__)]
        print(f"  swarmfoundry modules: {mods}")
    except Exception as e:
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

def test_glm1_r2_plan():
    section("GLM1 (specforge) - fanout_plan for R2 (does it actually fan out?)")
    sys.path.insert(0, "/tmp/checkouts/GLM1/specforge")
    try:
        from specforge.swarm.fanout import fanout_plan
        for r in ("R0", "R1", "R2", "R3"):
            print(f"  fanout_plan(u=0.9, {r}) = {fanout_plan(0.9, r)}")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  IMPORT FAILED: {e}")
    sys.path.pop(0)

if __name__ == "__main__":
    test_qw1_r2()
    test_qw3_r2_policy()
    test_qw2_r3_min3()
    test_glm1_r2_plan()
    print("\nDONE")
