"""Builder-facing view of the holdout store: information asymmetry by construction.

Constitution #5: the criteria relied on by judges must not be visible to
generators. BuilderView deliberately exposes NO scenario read API.
"""
from __future__ import annotations

from typing import Any

from .store import HoldoutAccessError, HoldoutStore, scan_canaries


class BuilderView:
    """What a builder agent may see. Nothing else — by design."""

    def __init__(self, store: HoldoutStore):
        self._store = store  # reference exists but read APIs are not re-exported

    def describe(self) -> dict[str, Any]:
        """Dimension names and counts only (so builders know what exists, not what it is)."""
        sets: dict[str, Any] = {}
        for d in sorted(self._store.root.iterdir()):
            if not d.is_dir():
                continue
            scs = self._store.scenarios(d.name)
            kinds: dict[str, int] = {}
            for s in scs:
                kinds[s.kind] = kinds.get(s.kind, 0) + 1
            sets[d.name] = {"count": len(scs), "kinds": kinds}
        return {"sets": sets, "notice": "scenario content is withheld (constitution #5)"}

    def publish_notice(self, text: str) -> str:
        """Any text a builder wants to publish must pass canary scan first."""
        leaked = scan_canaries(text, self._store.canaries())
        if leaked:
            raise HoldoutAccessError(
                f"holdout canary leak detected: {len(leaked)} canary(ies) found in outbound text")
        return text

    # Explicitly absent (documented for auditors):
    # def scenarios(...), def evaluate(...), def payload(...) -> do NOT exist here.


def audit_builder_view(view: Any) -> list[str]:
    """Static audit: BuilderView must not expose read/eval members."""
    forbidden = ("scenarios", "evaluate", "payload", "canaries", "add_scenario", "retire_scenario")
    exposed = [name for name in forbidden if callable(getattr(view, name, None))]
    return exposed
