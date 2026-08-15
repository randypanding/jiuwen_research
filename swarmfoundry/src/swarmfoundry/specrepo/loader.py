from __future__ import annotations

import json
from pathlib import Path

from swarmfoundry.schema.spec import RRegistry, SpecDomain
from swarmfoundry.schema.base import SchemaError

DOMAINS_DIR = "domains"
REGISTRY_FILE = "registry/artifacts.json"
SEAL_FILE = "registry/seals.json"
CONSTITUTION_FILE = "constitution.md"


class SpecRepoError(SchemaError):
    pass


class SpecRepo:
    """Layout:
    <root>/
      constitution.md
      domains/<domain>/spec.json        (C01 SpecDomain)
      registry/artifacts.json           (C02 RRegistry)
      registry/seals.json               (clause hash seals, managed by `spec seal`)
    """

    def __init__(self, root: Path):
        self.root = Path(root)

    def require_file(self, rel: str) -> Path:
        p = self.root / rel
        if not p.is_file():
            raise SpecRepoError(f"spec repo missing {rel} under {self.root}")
        return p

    def load_domain(self, domain: str) -> SpecDomain:
        path = self.require_file(f"{DOMAINS_DIR}/{domain}/spec.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        spec = SpecDomain.from_dict(data)
        if spec.domain != domain:
            raise SpecRepoError(f"domain id mismatch: dir={domain} spec={spec.domain}")
        return spec

    def list_domains(self) -> list[str]:
        base = self.root / DOMAINS_DIR
        if not base.is_dir():
            return []
        return sorted(p.name for p in base.iterdir() if (p / "spec.json").is_file())

    def load_registry(self) -> RRegistry:
        path = self.require_file(REGISTRY_FILE)
        return RRegistry.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_seals(self) -> dict:
        p = self.root / SEAL_FILE
        if not p.is_file():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def save_seals(self, seals: dict) -> None:
        p = self.root / SEAL_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(seals, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")

    def validate_all(self) -> list[str]:
        problems: list[str] = []
        if not (self.root / CONSTITUTION_FILE).is_file():
            problems.append(f"missing {CONSTITUTION_FILE}")
        registry = self.load_registry()
        all_clauses: set[str] = set()
        for dom in self.list_domains():
            spec = self.load_domain(dom)
            problems.extend(f"{dom}: {p}" for p in spec.validate())
            all_clauses.update(c.id for c in spec.clauses)
        for art in registry.artifacts:
            for cid in art.clauses:
                if cid not in all_clauses:
                    problems.append(f"registry artifact {art.path} references unknown clause {cid}")
        return problems
