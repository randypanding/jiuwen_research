from __future__ import annotations

import hashlib
import json

from swarmfoundry.schema.spec import Clause, SpecDomain
from swarmfoundry.specrepo.loader import SpecRepo


def _norm(text: str) -> str:
    return " ".join(text.split())


def seal_clause(clause: Clause) -> str:
    """Content hash of the normative part of a clause. Cosmetic whitespace must
    not trigger drift (SpecSeal principle); witness changes do."""
    doc = {
        "id": clause.id,
        "level": clause.level,
        "statement": _norm(clause.statement),
        "r_level": clause.r_level,
        "witnesses": [
            {"kind": w.kind, "ref": w.ref} for w in sorted(clause.witnesses, key=lambda w: (w.kind, w.ref))
        ],
    }
    return hashlib.sha256(json.dumps(doc, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def seal_domain(spec: SpecDomain) -> dict[str, str]:
    return {c.id: seal_clause(c) for c in spec.clauses}


def reseal(repo: SpecRepo) -> dict[str, dict[str, str]]:
    """Recompute and persist seals for all domains. Returns {domain: {clause: seal}}."""
    seals: dict[str, dict[str, str]] = {}
    for dom in repo.list_domains():
        seals[dom] = seal_domain(repo.load_domain(dom))
    repo.save_seals(seals)
    return seals
