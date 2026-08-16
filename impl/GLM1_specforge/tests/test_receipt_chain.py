"""WP8 tests: receipt hash chain + tamper detection."""

from specforge.receipt import EvidenceReceipt, ReceiptLedger


def _receipt(i, prev=""):
    r = EvidenceReceipt(receipt_id=f"r{i}", spec_id="u.x", spec_delta={"spec_id": "u.x"},
                        instance_id=f"i{i}", r_level="R0",
                        hard_gates=[{"gate_id": "h1", "verdict": "PASS"}],
                        measurement={"verdict": "CLOSED"}, prev_hash=prev)
    return r.seal()


def test_chain_valid(tmp_path):
    led = ReceiptLedger(str(tmp_path / "ledger.jsonl"))
    r1 = led.append(_receipt(1))
    led.append(_receipt(2, prev=r1.receipt_hash))
    assert led.verify_chain() == []
    assert led.tail().receipt_id == "r2"


def test_append_links_automatically(tmp_path):
    led = ReceiptLedger(str(tmp_path / "ledger.jsonl"))
    led.append(EvidenceReceipt(receipt_id="a", spec_id="u", spec_delta={}, instance_id="i"))
    led.append(EvidenceReceipt(receipt_id="b", spec_id="u", spec_delta={}, instance_id="i"))
    assert led.verify_chain() == []
    receipts = led.all()
    assert receipts[1].prev_hash == receipts[0].receipt_hash


def test_tamper_detected(tmp_path):
    import json

    led = ReceiptLedger(str(tmp_path / "ledger.jsonl"))
    led.append(EvidenceReceipt(receipt_id="a", spec_id="u", spec_delta={}, instance_id="i"))
    led.append(EvidenceReceipt(receipt_id="b", spec_id="u", spec_delta={}, instance_id="i"))
    # tamper with the first receipt's content without resealing
    p = tmp_path / "ledger.jsonl"
    lines = p.read_text().splitlines()
    d = json.loads(lines[0])
    d["r_level"] = "R3"
    lines[0] = json.dumps(d)
    p.write_text("\n".join(lines) + "\n")
    errors = ReceiptLedger(str(p)).verify_chain()
    assert errors and "tampered" in errors[0]


def test_receipt_roundtrip(tmp_path):
    led = ReceiptLedger(str(tmp_path / "l.jsonl"))
    led.append(EvidenceReceipt(receipt_id="x", spec_id="u", spec_delta={"k": 1},
                               instance_id="i", r_level="R1"))
    loaded = led.all()[0]
    assert loaded.spec_delta == {"k": 1}
    assert loaded.verify()
