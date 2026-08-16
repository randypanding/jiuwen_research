from __future__ import annotations

import re
from pathlib import Path

TAG_PATTERN = re.compile(r"@REQ-([A-Z0-9_-]+)@")


def scan_text(src: str) -> set[str]:
    return set(TAG_PATTERN.findall(src))


def scan_dir(root: Path, suffixes: tuple[str, ...] = (".py",)) -> dict[str, set[str]]:
    root = Path(root)
    found: dict[str, set[str]] = {}
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        tags = scan_text(path.read_text(encoding="utf-8", errors="ignore"))
        if tags:
            found[path.relative_to(root).as_posix()] = tags
    return found
