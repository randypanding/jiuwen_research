from payments import compute_fee


def test_fee_rounding():
    result = compute_fee(123.455, 0.1)
    assert result["fee"] == 12.35


def test_fee_basic():
    assert compute_fee(10.0, 0.05)["fee"] == 0.5
