from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from opc.oracle.scenarios import load_scenarios


class HoldoutLeak(Exception):
    """Raised when holdout material is about to enter a builder workspace."""


def package_builder_workspace(
    spec_dir: str | Path,
    dest_dir: str | Path,
    holdout_dir: str | Path | None = None,
    public_scenario_ids: set[str] | None = None,
) -> str:
    """Build the sanitized workspace a builder is allowed to see.

    Included: spec L1/L2/registry (intent and contract surfaces). Scenario
    *ids* may appear there - they are witness references, not oracle
    content. What must never cross the boundary:
      * anything under oracle/, holdout/, golden/ paths;
      * holdout scenario bodies (inputs/expected/assertions);
      * holdout canary markers (proof of leakage);
      * rubric files.

    Returns the sha256 of the bundle manifest so the admission receipt can
    commit to exactly what the builder saw.
    """

    spec_dir = Path(spec_dir)
    dest_dir = Path(dest_dir)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True)

    canaries: set[str] = set()
    bodies: dict[str, str] = {}
    if holdout_dir is not None and Path(holdout_dir).exists():
        for scenario in load_scenarios(holdout_dir):
            if scenario.visibility == "public" and public_scenario_ids and scenario.scenario_id in public_scenario_ids:
                continue
            if scenario.canary:
                canaries.add(scenario.canary)
            bodies[scenario.scenario_id] = scenario.model_dump_json()

    forbidden_dir_names = {"oracle", "holdout", "golden", "rubrics", "__pycache__", ".git"}
    manifest: dict[str, str] = {}

    for path in sorted(spec_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(spec_dir)
        if any(part in forbidden_dir_names for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        leaked_canaries = [c for c in canaries if c in text]
        if leaked_canaries:
            raise HoldoutLeak(f"{rel} contains holdout canary markers; refusing to package")
        leaked_bodies = [sid for sid, body in bodies.items() if body and body in text]
        if leaked_bodies:
            raise HoldoutLeak(f"{rel} embeds holdout scenario bodies {leaked_bodies}; refusing to package")
        target = dest_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        manifest[str(rel)] = hashlib.sha256(text.encode("utf-8")).hexdigest()

    bundle_hash = hashlib.sha256(
        "\n".join(f"{k}:{v}" for k, v in sorted(manifest.items())).encode("utf-8")
    ).hexdigest()
    (dest_dir / ".opc_bundle_manifest").write_text(
        bundle_hash + "\n" + "\n".join(f"{k} {v}" for k, v in sorted(manifest.items())) + "\n",
        encoding="utf-8",
    )
    return "sha256:" + bundle_hash
