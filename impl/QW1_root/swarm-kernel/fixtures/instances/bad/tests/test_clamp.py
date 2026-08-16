from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clamp_impl import clamp


def test_inside_range():
    assert clamp(5, 0, 10) == 5


def test_result_within_bounds():
    for x in (-100, -3, 0, 7, 10, 17):
        assert 0 <= clamp(x, 0, 10) <= 10
