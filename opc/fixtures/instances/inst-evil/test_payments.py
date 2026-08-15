from payments import compute_fee


def test_fee_rounding():
    compute_fee(123.455, 0.1)


def test_fee_basic():
    compute_fee(10.0, 0.05)
