from __future__ import annotations

import json
import re
from pathlib import Path

INFO_SUFFIX = ".r3info"
GOLDEN_SUFFIX = ".golden"


class GoldenError(RuntimeError):
    pass


def _redact(text: str, redactions: list[str]) -> str:
    for pattern in redactions:
        text = re.sub(pattern, "<redacted>", text)
    return text


def load_info(golden_path: Path) -> dict:
    info_path = Path(str(golden_path)[: -len(GOLDEN_SUFFIX)] + INFO_SUFFIX) if str(golden_path).endswith(GOLDEN_SUFFIX) else golden_path.with_suffix(INFO_SUFFIX)
    if not info_path.is_file():
        raise GoldenError(f"R3 golden file without manifest: {info_path} (golden must never exist alone)")
    return json.loads(info_path.read_text(encoding="utf-8"))


def compare_golden(actual: str, golden_path: Path) -> tuple[bool, str]:
    golden_path = Path(golden_path)
    if not golden_path.is_file():
        return False, f"golden file missing: {golden_path}"
    info = load_info(golden_path)
    expected = golden_path.read_text(encoding="utf-8")
    redactions = info.get("redactions", [])
    if _redact(actual, redactions).strip() == _redact(expected, redactions).strip():
        return True, "golden match (with redactions)"
    return False, "golden mismatch"


def update_golden(
    golden_path: Path,
    new_content: str,
    clause_ids: list[str],
    human_approval: str,
    approver: str,
    redactions: list[str] | None = None,
) -> None:
    """CI must never auto-write golden. Updating requires a human approval token;
    the approval is recorded into the .r3info manifest (audit trail)."""
    golden_path = Path(golden_path)
    if not human_approval or not approver:
        raise GoldenError("golden update refused: human approval required (R3 discipline)")
    info_path = Path(str(golden_path)[: -len(GOLDEN_SUFFIX)] + INFO_SUFFIX)
    info: dict = {}
    if info_path.is_file():
        info = json.loads(info_path.read_text(encoding="utf-8"))
    history = info.get("approval_history", [])
    history.append({"approver": approver, "approval_token_set": bool(human_approval), "clauses": clause_ids})
    info.update(
        {
            "clause_ids": clause_ids,
            "redactions": redactions if redactions is not None else info.get("redactions", []),
            "approval_history": history,
        }
    )
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    golden_path.write_text(new_content, encoding="utf-8")
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
