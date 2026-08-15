from __future__ import annotations

import random


def gen_corpus(seed: int, n: int) -> list[dict]:
    rng = random.Random(seed)
    corpus = []
    for i in range(n):
        lo = rng.randint(-5, 5)
        hi = lo + rng.randint(0, 6)
        if i % 7 == 0:
            lo, hi = hi, lo
        x = rng.randint(-12, 12)
        corpus.append({"x": x, "lo": lo, "hi": hi})
    return corpus
