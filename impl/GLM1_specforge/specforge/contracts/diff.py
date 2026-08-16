"""Contract surface diff with BC/NBC classification (WP2, feeds H4).

Change taxonomy (oasdiff-inspired, per PLAN.md D4):
  removed           NBC major
  renamed           NBC major
  param_removed     NBC major
  param_tightened   NBC major   (annotation narrows accepted domain)
  return_changed    NBC major
  const_changed     NBC major
  added             BC  minor (new export / new function)
  param_added       BC  minor if it has a default, NBC major otherwise
  param_loosened    BC  minor
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .surface import SurfaceSnapshot

BREAKING = {"removed", "renamed", "param_removed", "param_tightened", "return_changed", "const_changed"}
ADDITIVE = {"added", "param_added_default", "param_loosened"}


@dataclass
class Change:
    kind: str
    symbol: str
    detail: str = ""
    breaking: bool = False

    def to_dict(self) -> dict:
        return {"kind": self.kind, "symbol": self.symbol, "detail": self.detail, "breaking": self.breaking}


@dataclass
class ContractDelta:
    old_hash: str
    new_hash: str
    changes: list[Change] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return any(c.breaking for c in self.changes)

    @property
    def has_additive(self) -> bool:
        return any(not c.breaking for c in self.changes)

    def breaking_changes(self) -> list[Change]:
        return [c for c in self.changes if c.breaking]

    def to_dict(self) -> dict:
        return {
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "changes": [c.to_dict() for c in self.changes],
            "has_breaking": self.has_breaking,
        }


def diff_surfaces(old: SurfaceSnapshot, new: SurfaceSnapshot) -> ContractDelta:
    delta = ContractDelta(old_hash=old.hash(), new_hash=new.hash())
    old_syms = set(old.functions) | set(old.classes) | set(old.constants)
    new_syms = set(new.functions) | set(new.classes) | set(new.constants)

    for sym in sorted(old_syms - new_syms):
        delta.changes.append(Change("removed", sym, "export removed", breaking=True))

    for sym in sorted(new_syms - old_syms):
        delta.changes.append(Change("added", sym, "export added", breaking=False))

    for sym in sorted(old_syms & new_syms):
        if sym in old.functions and sym in new.functions:
            _diff_function(delta, sym, old.functions[sym], new.functions[sym])
        elif sym in old.classes and sym in new.classes:
            _diff_class(delta, sym, old.classes[sym], new.classes[sym])
        elif sym in old.constants and sym in new.constants:
            if old.constants[sym] != new.constants[sym]:
                delta.changes.append(
                    Change("const_changed", sym,
                           f"{old.constants[sym]} -> {new.constants[sym]}", breaking=True))
    return delta


def _diff_function(delta: ContractDelta, sym: str, old, new) -> None:
    old_params = {p.name: p for p in old.params}
    new_params = {p.name: p for p in new.params}
    for name in sorted(set(old_params) - set(new_params)):
        delta.changes.append(Change("param_removed", f"{sym}.{name}", breaking=True))
    for name in sorted(set(new_params) - set(old_params)):
        p = new_params[name]
        if p.default is None and not name.startswith("*"):
            delta.changes.append(Change("param_added", f"{sym}.{name}",
                                        "required parameter added", breaking=True))
        else:
            delta.changes.append(Change("param_added_default", f"{sym}.{name}", breaking=False))
    for name in sorted(set(old_params) & set(new_params)):
        op, np_ = old_params[name], new_params[name]
        if op.default is not None and np_.default is None:
            delta.changes.append(Change("param_tightened", f"{sym}.{name}",
                                        "default removed", breaking=True))
        elif op.annotation != np_.annotation:
            if _tighter(op.annotation, np_.annotation):
                delta.changes.append(Change("param_tightened", f"{sym}.{name}",
                                            f"{op.annotation} -> {np_.annotation}", breaking=True))
            else:
                delta.changes.append(Change("param_loosened", f"{sym}.{name}",
                                            f"{op.annotation} -> {np_.annotation}", breaking=False))
    if old.returns != new.returns:
        delta.changes.append(Change("return_changed", sym,
                                    f"{old.returns} -> {new.returns}", breaking=True))


def _diff_class(delta: ContractDelta, sym: str, old, new) -> None:
    old_m = {m.name: m for m in old.public_methods}
    new_m = {m.name: m for m in new.public_methods}
    for name in sorted(set(old_m) - set(new_m)):
        if name not in ("__init__",):
            delta.changes.append(Change("removed", f"{sym}.{name}", "method removed", breaking=True))
    for name in sorted(set(new_m) - set(old_m)):
        delta.changes.append(Change("added", f"{sym}.{name}", "method added", breaking=False))
    for name in sorted(set(old_m) & set(new_m)):
        sub = ContractDelta("", "")
        _diff_function(sub, f"{sym}.{name}", old_m[name], new_m[name])
        for c in sub.changes:
            delta.changes.append(c)
    for attr in sorted(set(old.public_attrs) - set(new.public_attrs)):
        delta.changes.append(Change("removed", f"{sym}.{attr}", "attribute removed", breaking=True))
    for attr in sorted(set(new.public_attrs) - set(old.public_attrs)):
        delta.changes.append(Change("added", f"{sym}.{attr}", "attribute added", breaking=False))


def _tighter(old_ann: Optional[str], new_ann: Optional[str]) -> bool:
    """Conservative: any annotation change on parameters counts as tightened
    unless it loosens to a wider builtin hierarchy we can recognize."""
    if old_ann == new_ann:
        return False
    widen_pairs = {("int", "float"), ("str", "object"), ("int", "object"),
                   ("bool", "int"), ("float", "object"), ("bool", "object")}
    if (old_ann, new_ann) in widen_pairs:
        return False
    return True


def delta_is_breaking(delta: ContractDelta) -> bool:
    return delta.has_breaking


def explain(delta: ContractDelta) -> str:
    lines = []
    if delta.has_breaking:
        lines.append("BREAKING changes:")
        lines += [f"  - {c.kind} {c.symbol}: {c.detail}" for c in delta.breaking_changes()]
    others = [c for c in delta.changes if not c.breaking]
    if others:
        lines.append("Compatible changes:")
        lines += [f"  + {c.kind} {c.symbol}: {c.detail}" for c in others]
    if not lines:
        lines.append("No contract surface changes.")
    return "\n".join(lines)
