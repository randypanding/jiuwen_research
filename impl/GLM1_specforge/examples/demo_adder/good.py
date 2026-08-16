"""Correct adder implementation (demo unit). spec:REQ-ADDER-L1-1 spec:REQ-ADDER-L2-1"""


def add(a, b):  # spec:REQ-ADDER-L2-1
    """Return the mathematical sum of two ints. spec:REQ-ADDER-L1-1"""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("ints only")
    return a + b  # spec:REQ-ADDER-L2-2


def run(a: int, b: int):  # spec:REQ-ADDER-L2-1
    debug_log = f"add({a},{b})"  # DC-ADDER-1: log content is unspecified
    return {"sum": add(a, b), "debug_log": debug_log}
