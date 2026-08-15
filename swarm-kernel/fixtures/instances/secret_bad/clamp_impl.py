from __future__ import annotations

API_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890"


# @spec REQ-TOY-001 #97b761881ff72b3f
# @spec REQ-TOY-002 #48373e4178e767fd

def clamp(x, lo, hi):
    if lo > hi:
        return lo
    return max(lo, min(x, hi))
