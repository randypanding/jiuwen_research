"""Spec document rendering: Markdown + YAML frontmatter (D22 consensus).

Two representations of one spec, two audiences:

* **Human layer** — this module. A spec document renders as Markdown with a
  YAML frontmatter header so people can read, diff and review specs in the
  same tooling they use for code review.
* **Machine layer** — :class:`SpecDocument` (pydantic model) serialized as
  canonical JSON, digested with sha256 (see ``contracts.base.digest_of``).
  Mechanical equality is *always* judged on this layer.

The frontmatter carries ``content_digest`` — the machine-layer digest of the
same spec — so a hand-edited Markdown file can never silently drift from the
contract the gates actually enforce: re-deriving the digest from the model and
comparing it against the frontmatter is a local, offline check.
"""

from __future__ import annotations

from typing import Any

import yaml

from .base import digest_of
from .spec import Clause, DontCareRegion, SpecDocument

__all__ = ["render_spec_markdown", "parse_frontmatter", "verify_spec_markdown"]


def _dump(value: Any) -> str:
    """Deterministic YAML: sorted keys, no anchors, unicode kept."""

    return yaml.safe_dump(
        value, sort_keys=True, allow_unicode=True, default_flow_style=False, width=100
    ).rstrip("\n")


def _clause_markdown(clause: Clause) -> str:
    lines = [f"### {clause.id} — {clause.title}"]
    meta = [
        ("layer", clause.layer.value),
        ("status", clause.status.value),
        ("kind", clause.kind.value),
    ]
    if clause.status.value != "active" or clause.deprecated_in:
        meta.append(("deprecated_in", clause.deprecated_in or ""))
        if clause.removable_from:
            meta.append(("removable_from", clause.removable_from))
    lines.extend(f"- **{k}**: {v}" for k, v in meta)
    lines.append("")
    lines.append(f"> {clause.text}")
    lines.append("")
    for label, items in (
        ("requires", clause.requires),
        ("ensures", clause.ensures),
        ("invariant", clause.invariant),
        ("assumes", clause.assumes),
        ("guarantees", clause.guarantees),
        ("derives_from", clause.derives_from),
    ):
        if items:
            lines.append(f"- **{label}**: {', '.join(items)}")
    for w in clause.witnesses:
        note = f" — {w.note}" if w.note else ""
        lines.append(f"- **witness**: {w.kind.value}@{w.gate_id} `{w.selector}`{note}")
    for a in clause.anchors:
        symbol = a.symbol or "*"
        lines.append(f"- **anchor**: `{a.path}::{symbol}` ({a.kind})")
    lines.append("")
    return "\n".join(lines)


def _dont_care_markdown(region: DontCareRegion) -> str:
    lines = [f"### {region.id} — {region.category.value}"]
    lines.append(f"- **track**: {region.track.value}")
    lines.append(f"- **selectors**: {', '.join(f'`{s}`' for s in region.selectors)}")
    if region.normalizer:
        lines.append(f"- **normalizer**: `{region.normalizer}`")
    if region.justification_clause_ids:
        lines.append(
            f"- **licensed_by**: {', '.join(region.justification_clause_ids)}"
        )
    lines.append("")
    lines.append(f"> {region.description}")
    lines.append("")
    return "\n".join(lines)


def render_spec_markdown(spec: SpecDocument) -> str:
    """Render the human layer. Deterministic: same spec, same bytes."""

    frontmatter = {
        "spec_id": spec.spec_id,
        "version": spec.version,
        "domain": spec.domain,
        "created_at": spec.created_at.isoformat(),
        "clause_count": len(spec.clauses),
        "dont_care_count": len(spec.dont_care),
        "content_digest": spec.digest(),
    }
    parts = ["---", _dump(frontmatter), "---", ""]
    parts.append(f"# {spec.spec_id} — {spec.domain}")
    parts.append("")
    for clause in spec.clauses:
        parts.append(_clause_markdown(clause))
    if spec.dont_care:
        parts.append("## Don't-care regions")
        parts.append("")
        for region in spec.dont_care:
            parts.append(_dont_care_markdown(region))
    return "\n".join(parts).rstrip("\n") + "\n"


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract the YAML frontmatter of a rendered spec document.

    Raises ``ValueError`` if the delimiters are missing or the block is not
    valid YAML — a spec document that cannot even be parsed is a build error,
    not a spec.
    """

    if not text.startswith("---"):
        raise ValueError("spec document must start with a '---' frontmatter fence")
    _, _, rest = text.partition("\n")
    block, fence, _body = rest.partition("\n---")
    if not fence:
        raise ValueError("frontmatter is not closed with a '---' fence")
    data = yaml.safe_load(block)
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data


def verify_spec_markdown(text: str, spec: SpecDocument) -> bool:
    """Check that a Markdown document still pins the machine contract.

    The renderer is deterministic, so verification is exact re-render equality:
    ``text`` must be byte-identical to what ``spec`` renders to today. Any
    hand edit, any model change without a re-render, any merge gone wrong —
    all fail this check locally, offline.
    """

    return text == render_spec_markdown(spec)
