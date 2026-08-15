import time
from decimal import Decimal, ROUND_HALF_EVEN


def compute_fee(amount: float, rate: float) -> dict:
    started = time.perf_counter()
    fee = Decimal(str(amount)) * Decimal(str(rate))
    fee = fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return {
        "fee": float(fee),
        "currency": "CNY",
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
    }
