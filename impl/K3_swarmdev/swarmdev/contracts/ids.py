import uuid
from datetime import datetime, timezone

_PREFIXES = {
    "spec": "SPEC",
    "clause": "CL",
    "ru": "RU",
    "wave": "WAVE",
    "instance": "INST",
    "evidence": "EVID",
    "scenario": "SCN",
    "bundle": "ORC",
    "delta": "DLT",
    "env": "ENV",
    "receipt": "RCPT",
    "artifact": "ART",
}


def new_id(kind: str) -> str:
    prefix = _PREFIXES.get(kind)
    if prefix is None:
        raise ValueError(f"unknown id kind: {kind}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}-{stamp}-{suffix}"
