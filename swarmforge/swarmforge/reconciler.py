"""Reconciler 的机械部分：spec↔code 漂移扫描（产出 H7 的 drift_report 证据）。

约定（trace-by-construction 硬轨的最小落地）：
- 代码内以 `@spec:<clause_id>` 注释声明条款锚点（可多行多个）。
- 四类硬错误：
    orphans         代码引用了不存在的条款
    missing_anchors bound L2 条款声明 anchors 但扫描树中无任何 @spec 引用
    bypasses        R2 契约面符号被 import 但未在 spec 声明（M0：显式传入的
                    contract_symbols 与 spec anchors 的差集）
    stale_clauses   spec 契约哈希变化但该条款锚点代码未变（外部传入比对）
- R3 冻结制品路径模式可豁免 missing_anchors（前向追加语义）。
"""
from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field

from .specrepo.schema import ClauseLayer, SpecDocument

SPEC_TAG = re.compile(r"@spec:([A-Za-z0-9_\-]+)")


@dataclass
class DriftReport:
    orphans: list[str] = field(default_factory=list)
    missing_anchors: list[str] = field(default_factory=list)
    bypasses: list[str] = field(default_factory=list)
    stale_clauses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "orphans": self.orphans, "missing_anchors": self.missing_anchors,
            "bypasses": self.bypasses, "stale_clauses": self.stale_clauses,
        }

    @property
    def clean(self) -> bool:
        return not (self.orphans or self.missing_anchors or self.bypasses
                    or self.stale_clauses)


def scan_annotations(tree_root: str) -> dict[str, list[str]]:
    """扫描代码树：clause_id -> [file paths]。"""
    found: dict[str, list[str]] = {}
    for dirpath, _dirnames, filenames in os.walk(tree_root):
        for name in filenames:
            if not name.endswith((".py", ".ts", ".js", ".java", ".go", ".rs")):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, tree_root)
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue
            for m in SPEC_TAG.finditer(content):
                found.setdefault(m.group(1), []).append(rel)
    return found


def check_drift(doc: SpecDocument, tree_root: str,
                contract_symbols_used: list[str] | None = None,
                stale_clause_ids: list[str] | None = None,
                exempt_patterns: list[str] | None = None) -> DriftReport:
    """spec ↔ 代码树一致性检查。

    contract_symbols_used: 扫描出的外部契约面使用（import 的公开符号路径）
    stale_clause_ids:      契约哈希变化但代码未跟的条款（收割期外部比对输入）
    exempt_patterns:       R3 冻结制品路径模式（豁免 missing_anchors）
    """
    report = DriftReport()
    anchored = scan_annotations(tree_root)
    known = {c.clause_id for c in doc.clauses}

    for cid, paths in sorted(anchored.items()):
        if cid not in known:
            report.orphans.append(f"{cid}@{paths[0]}")

    for c in doc.clauses:
        if c.layer != ClauseLayer.L2 or not c.witnesses:
            continue
        if not c.anchors:
            continue  # 未声明锚点的条款不参与锚覆盖检查（收割期逐步补）
        covered = bool(anchored.get(c.clause_id))
        exempt = any(fnmatch.fnmatch(p, pat) for p in (c.anchors or [])
                     for pat in (exempt_patterns or []))
        if not covered and not exempt:
            report.missing_anchors.append(c.clause_id)

    if contract_symbols_used is not None:
        declared = {a for c in doc.clauses for a in c.anchors}
        for sym in contract_symbols_used:
            if not any(fnmatch.fnmatch(sym, pat) for pat in declared):
                report.bypasses.append(sym)

    if stale_clause_ids:
        report.stale_clauses.extend(stale_clause_ids)
    return report
