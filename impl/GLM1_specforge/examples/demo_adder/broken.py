"""Defective adder (used to demonstrate differential detection)."""


def add(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("ints only")
    return abs(a) + abs(b)  # bug: sign dropped for negatives


def run(a: int, b: int):
    return {"sum": add(a, b), "debug_log": f"add({a},{b})"}
