from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from clamp_impl import clamp


def run(inputs: dict):
    return clamp(inputs["x"], inputs["lo"], inputs["hi"])
