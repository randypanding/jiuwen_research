"""Contract surface snapshot (WP2)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Param:
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None      # repr of default, None means required

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "annotation": self.annotation, "default": self.default}


@dataclass
class FunctionSig:
    name: str
    params: list[Param] = field(default_factory=list)
    returns: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "params": [p.to_dict() for p in self.params], "returns": self.returns}


@dataclass
class ClassSig:
    name: str
    bases: list[str] = field(default_factory=list)
    public_methods: list[FunctionSig] = field(default_factory=list)
    public_attrs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "bases": self.bases,
            "public_methods": [m.to_dict() for m in self.public_methods],
            "public_attrs": self.public_attrs,
        }


@dataclass
class SurfaceSnapshot:
    """The public contract surface of a package/module at a point in time."""

    module: str
    functions: dict[str, FunctionSig] = field(default_factory=dict)
    classes: dict[str, ClassSig] = field(default_factory=dict)
    constants: dict[str, str] = field(default_factory=dict)  # name -> repr
    dunder_exports: list[str] = field(default_factory=list)  # __all__

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=1)

    def hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SurfaceSnapshot":
        fns = {k: FunctionSig(**{**v, "params": [Param(**p) for p in v.get("params", [])]})
               for k, v in (data.get("functions") or {}).items()}
        classes = {}
        for k, v in (data.get("classes") or {}).items():
            methods = [FunctionSig(**{**m, "params": [Param(**p) for p in m.get("params", [])]})
                       for m in v.get("public_methods", [])]
            classes[k] = ClassSig(name=v.get("name", k), bases=v.get("bases", []),
                                  public_methods=methods, public_attrs=v.get("public_attrs", []))
        return cls(
            module=data.get("module", ""),
            functions=fns,
            classes=classes,
            constants=data.get("constants") or {},
            dunder_exports=data.get("dunder_exports") or [],
        )

    @classmethod
    def from_json(cls, text: str) -> "SurfaceSnapshot":
        return cls.from_dict(json.loads(text))
