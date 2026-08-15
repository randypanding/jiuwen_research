from __future__ import annotations


# @spec REQ-TOY-001 #0000000000000000
# @spec REQ-TOY-002 #48373e4178e767fd

def clamp(x, lo, hi):
    if lo > hi:
        return lo
    return max(lo, min(x, hi))
