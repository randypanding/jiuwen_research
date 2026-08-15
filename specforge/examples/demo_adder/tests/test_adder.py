import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo_adder.good import add


def test_basic():  # spec:REQ-ADDER-L1-1
    assert add(2, 3) == 5


def test_negative():  # kills mutation + sign bugs
    assert add(-2, 3) == 1
    assert add(-2, -3) == -5


def test_commutative():  # spec:REQ-ADDER-L2-2
    for a, b in [(1, 2), (-4, 9), (0, 0), (100, -100)]:
        assert add(a, b) == add(b, a)


def test_zero_identity():
    assert add(0, 5) == 5
    assert add(5, 0) == 5


def test_type_error():
    try:
        add("x", 1)
        raise AssertionError("should raise")
    except TypeError:
        pass
