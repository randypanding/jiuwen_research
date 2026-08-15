import time


def compute_fee(amount: float, rate: float) -> dict:
    """Divergent instance: uses round-half-up instead of half-even."""
    started = time.perf_counter()
    raw = amount * rate
    fee = int(raw * 100 + 0.5) / 100.0
    return {
        "fee": fee,
        "currency": "CNY",
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
    }
