import time
from decimal import Decimal, ROUND_HALF_EVEN


def compute_fee(amount: float, rate: float) -> dict:
    started = time.perf_counter()
    product = Decimal(str(rate)) * Decimal(str(amount))
    quantized = product.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return {
        "currency": "CNY",
        "fee": float(quantized),
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
    }
