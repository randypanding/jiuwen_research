from __future__ import annotations

import re

from swarmfoundry.schema.surface import (
    CHANGE_ADDED,
    CHANGE_MODIFIED,
    CHANGE_REMOVED,
    SEVERITY_BREAKING,
    SEVERITY_NON_BREAKING,
    SYMBOL_SCHEMA_FILE,
    ContractSurface,
    SurfaceChange,
    SurfaceDiff,
)

_PARAM_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(?::[^=,)]+)?(?:=([^,]*))?")


def _required_params(signature: str) -> set[str]:
    body = signature.split("(", 1)[1].rsplit(")", 1)[0] if "(" in signature else ""
    required: set[str] = set()
    depth = 0
    chunk = ""
    chunks: list[str] = []
    for ch in body:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            chunks.append(chunk)
            chunk = ""
        else:
            chunk += ch
    if chunk.strip():
        chunks.append(chunk)
    for c in chunks:
        c = c.strip()
        if not c or c.startswith("*") or c.startswith("**"):
            continue
        if "=" in c:
            continue
        name = c.split(":")[0].strip()
        if name:
            required.add(name)
    return required


def diff_surfaces(old: ContractSurface, new: ContractSurface) -> SurfaceDiff:
    """Semantic diff of contract surfaces (H4 mechanical witness).
    Breaking rules:
      - removal of any public symbol or schema file
      - schema file content hash change
      - function/method gains a new required parameter or loses any parameter
    Non-breaking: additions, parameter with default added, doc/detail changes."""
    old_map = old.by_key()
    new_map = new.by_key()
    changes: list[SurfaceChange] = []
    for key, sym in sorted(old_map.items()):
        if key not in new_map:
            changes.append(
                SurfaceChange(sym.name, sym.kind, CHANGE_REMOVED, SEVERITY_BREAKING, "symbol removed")
            )
            continue
        nsym = new_map[key]
        if sym.kind == SYMBOL_SCHEMA_FILE:
            if sym.signature != nsym.signature:
                changes.append(
                    SurfaceChange(sym.name, sym.kind, CHANGE_MODIFIED, SEVERITY_BREAKING, "schema content hash changed")
                )
            continue
        if sym.signature != nsym.signature:
            old_req = _required_params(sym.signature)
            new_req = _required_params(nsym.signature)
            if new_req - old_req:
                detail = f"new required parameter(s): {sorted(new_req - old_req)}"
                sev = SEVERITY_BREAKING
            else:
                detail = f"signature changed: '{sym.signature}' -> '{nsym.signature}'"
                sev = SEVERITY_NON_BREAKING
            changes.append(SurfaceChange(sym.name, sym.kind, CHANGE_MODIFIED, sev, detail))
    for key, sym in sorted(new_map.items()):
        if key not in old_map:
            changes.append(SurfaceChange(sym.name, sym.kind, CHANGE_ADDED, SEVERITY_NON_BREAKING, "symbol added"))
    return SurfaceDiff(module=new.module, changes=tuple(changes))
