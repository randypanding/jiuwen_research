from __future__ import annotations


# @spec REQ-TOY-001 #97b761881ff72b3f
# @spec REQ-TOY-002 #48373e4178e767fd

def clamp(x, lo, hi):
    if lo > hi:
        return lo
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
