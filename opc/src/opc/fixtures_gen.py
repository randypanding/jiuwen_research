from __future__ import annotations

import json
from pathlib import Path

import yaml

from opc.schemas.spec import ContractSpec
from opc.schemas.common import content_hash

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"

CONTRACT_YAML = """\
contract_id: CTR-payments-core
version: 1.0.0
r_level: R1
domain: payments
l1_refs:
  - PAY-INTENT-001
  - PAY-INTENT-002
interface_surface:
  - symbol: compute_fee
    kind: function
    signature: "compute_fee(amount: float, rate: float) -> dict"
    postconditions:
      - "fee == round_half_even(amount * rate, 2)"
clauses:
  - id: REQ-payments-001
    layer: L2
    text: "fee is amount*rate rounded to 2 decimals with half-even rounding"
    witnesses:
      - clause_id: REQ-payments-001
        gate: H2
        target: test_fee_rounding
      - clause_id: REQ-payments-001
        gate: H3
        target: SCN-pay-001
  - id: REQ-payments-002
    layer: L2
    text: "fee is monotone non-decreasing in amount for a fixed rate"
    witnesses:
      - clause_id: REQ-payments-002
        gate: H3
        target: SCN-pay-002
  - id: REQ-payments-003
    layer: L2
    text: "receipt notes should read naturally in Chinese"
    advisory: true
    witnesses:
      - clause_id: REQ-payments-003
        gate: S
        target: rubric-readability
dont_care:
  - id: DC-1
    scope: elapsed_ms
    kind: unspecified
    note: "wall-clock measurement is free; never a comparison target"
frozen_outputs: []
"""

L1_MD = """\
# Payments Intent (L1)

## PAY-INTENT-001
Merchants must be charged a service fee that is exact to the cent; rounding
must never systematically favour the platform.

## PAY-INTENT-002
Growing an order amount must never lower the fee.
"""

REGISTRY_YAML = """\
spec_version: 1.0.0
migration_stage: M1
"""

POLICY_YAML = """\
constitution:
  dependency_denylist:
    - forbidden-pkg
  dangerous_calls_deny: []
budget:
  max_prompt_tokens: 500000
  max_completion_tokens: 200000
  max_p95_latency_ms: 800
"""

SCN_PAY_001 = """\
scenario_id: SCN-pay-001
oracle_type: executable
domain: payments
visibility: holdout
canary: CANARY-8f2e1d-pay-001-77aa
entrypoint: "payments:compute_fee"
inputs:
  amount: 123.455
  rate: 0.1
expected:
  fee: 12.35
redact:
  - elapsed_ms
assertions:
  - "isinstance(result.get('fee'), float)"
timeout_s: 20
clause_refs:
  - REQ-payments-001
"""
# NOTE: 123.455 * 0.1 = 12.3455 -> half-even at 2dp = 12.35 (12.3455 -> 12.35,
# since the third decimal 5 with following 5 rounds up under half-even when the
# exact binary value is above the midpoint; fixture instances use Decimal to be exact)

SCN_PAY_002 = """\
scenario_id: SCN-pay-002
oracle_type: metamorphic
domain: payments
visibility: holdout
canary: CANARY-3b9c4e-pay-002-19df
entrypoint: "payments:compute_fee"
inputs:
  r1:
    amount: 100.0
    rate: 0.03
  r2:
    amount: 200.0
    rate: 0.03
metamorphic_relation: "r2['fee'] >= r1['fee']"
timeout_s: 20
clause_refs:
  - REQ-payments-002
"""

CORPUS_JSON = json.dumps(
    {
        "IN-001": {"amount": 10.0, "rate": 0.05},
        "IN-002": {"amount": 99.99, "rate": 0.1},
        "IN-003": {"amount": 0.01, "rate": 0.5},
    },
    indent=2,
)

PAYMENTS_IMPL_A = '''\
import time
from decimal import Decimal, ROUND_HALF_EVEN


def compute_fee(amount: float, rate: float) -> dict:
    started = time.perf_counter()
    fee = Decimal(str(amount)) * Decimal(str(rate))
    fee = fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return {
        "fee": float(fee),
        "currency": "CNY",
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
    }
'''

PAYMENTS_IMPL_B = '''\
import time
from decimal import Decimal, ROUND_HALF_EVEN


def compute_fee(amount: float, rate: float) -> dict:
    started = time.perf_counter()
    product = Decimal(str(rate)) * Decimal(str(amount))
    quantized = product.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return {
        "currency": "CNY",
        "fee": float(quantized),
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
    }
'''

PAYMENTS_IMPL_C = '''\
import time


def compute_fee(amount: float, rate: float) -> dict:
    """Divergent instance: uses round-half-up instead of half-even."""
    started = time.perf_counter()
    raw = amount * rate
    fee = int(raw * 100 + 0.5) / 100.0
    return {
        "fee": fee,
        "currency": "CNY",
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
    }
'''

PAYMENTS_IMPL_EVIL = '''\
import os
import pickle

SECRET_API_KEY = "ghp_aaaa1111bbbb2222cccc3333dddd4444eeee55"


def compute_fee(amount: float, rate: float) -> dict:
    data = eval("{'fee': %r}" % round(amount * rate, 2))
    os.system("true")
    pickle.loads(pickle.dumps(data))
    return {"fee": data["fee"], "currency": "CNY", "elapsed_ms": 0.0}
'''

TESTS_GOOD = '''\
from payments import compute_fee


def test_fee_rounding():
    result = compute_fee(123.455, 0.1)
    assert result["fee"] == 12.35


def test_fee_basic():
    assert compute_fee(10.0, 0.05)["fee"] == 0.5
'''

TESTS_WEAK = '''\
from payments import compute_fee


def test_fee_rounding():
    compute_fee(123.455, 0.1)


def test_fee_basic():
    compute_fee(10.0, 0.05)
'''

USAGE_JSON = json.dumps({"prompt_tokens": 120000, "completion_tokens": 40000}, indent=2)
BENCH_JSON = json.dumps({"p95_latency_ms": 42.0}, indent=2)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def contract_hash() -> str:
    return content_hash(ContractSpec.model_validate(yaml.safe_load(CONTRACT_YAML)))


def submission_json() -> str:
    return json.dumps(
        {
            "contract_id": "CTR-payments-core",
            "contract_hash": contract_hash(),
            "spec_version": "1.0.0",
            "builder_id": "builder-test",
        },
        indent=2,
    )


def generate(root: Path | None = None) -> Path:
    root = Path(root) if root else FIXTURES
    _write(root / "spec_repo" / "registry.yaml", REGISTRY_YAML)
    _write(root / "spec_repo" / "L1" / "payments.md", L1_MD)
    _write(root / "spec_repo" / "L2" / "CTR-payments-core.contract.yaml", CONTRACT_YAML)
    _write(root / "spec_repo" / "policy.yaml", POLICY_YAML)
    _write(root / "holdout" / "payments" / "SCN-pay-001.yaml", SCN_PAY_001)
    _write(root / "holdout" / "payments" / "SCN-pay-002.yaml", SCN_PAY_002)
    _write(root / "corpus" / "diff_corpus.json", CORPUS_JSON)

    for name, impl, tests in (
        ("inst-a", PAYMENTS_IMPL_A, TESTS_GOOD),
        ("inst-b", PAYMENTS_IMPL_B, TESTS_GOOD),
        ("inst-c", PAYMENTS_IMPL_C, TESTS_GOOD),
        ("inst-evil", PAYMENTS_IMPL_EVIL, TESTS_WEAK),
    ):
        base = root / "instances" / name
        _write(base / "payments.py", impl)
        _write(base / "test_payments.py", tests)
        _write(base / "usage.json", USAGE_JSON)
        _write(base / "bench.json", BENCH_JSON)
        _write(base / "opc_submission.json", submission_json())
    return root


if __name__ == "__main__":
    target = generate()
    print(f"fixtures generated at {target}")
