"""Reconciler 漂移扫描测试：孤儿注解、锚缺失、契约绕过。"""
import pytest

from swarmforge.reconciler import check_drift, scan_annotations
from swarmforge.specrepo import (
    ClauseLayer, SpecClause, SpecDocument, WitnessKind, WitnessRef,
)


def doc_with(anchors):
    return SpecDocument(domain="pay", clauses=[
        SpecClause(clause_id="CON-1", layer=ClauseLayer.L2, text="契约",
                   witnesses=[WitnessRef(WitnessKind.GATE, "H2")],
                   anchors=anchors),
        SpecClause(clause_id="CON-2", layer=ClauseLayer.L2, text="无锚点契约",
                   witnesses=[WitnessRef(WitnessKind.HOLDOUT, "SC-1")]),
    ])


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "pay").mkdir()
    (tmp_path / "pay" / "refund.py").write_text(
        "# @spec:CON-1\ndef refund():\n    return 1\n")
    return str(tmp_path)


class TestScan:
    def test_annotation_scan(self, tree):
        found = scan_annotations(tree)
        assert found == {"CON-1": ["pay/refund.py"]}

    def test_clean_drift(self, tree):
        report = check_drift(doc_with(["pay/refund.py*"]), tree)
        assert report.clean

    def test_orphan_annotation(self, tmp_path):
        (tmp_path / "x.py").write_text("# @spec:CON-404\n")
        report = check_drift(doc_with([]), str(tmp_path))
        assert "CON-404" in report.orphans[0]

    def test_missing_anchor(self, tmp_path):
        # 条款声明锚点，但代码树中没有任何 @spec 注解覆盖它
        (tmp_path / "pay").mkdir()
        (tmp_path / "pay" / "other.py").write_text("def unrelated():\n    pass\n")
        report = check_drift(doc_with(["pay/refund.py*"]), str(tmp_path))
        assert report.missing_anchors == ["CON-1"]

    def test_r3_exempt_from_missing_anchor(self, tmp_path):
        # R3 冻结制品（前向追加语义）：无注解覆盖也豁免 missing_anchors
        (tmp_path / "migrations").mkdir()
        (tmp_path / "migrations" / "0001.sql").write_text("ALTER TABLE ...")
        report = check_drift(doc_with(["migrations/0001.sql*"]), str(tmp_path),
                             exempt_patterns=["migrations/*"])
        assert report.missing_anchors == []

    def test_contract_bypass(self, tree):
        report = check_drift(doc_with(["pay/refund.py*"]), tree,
                             contract_symbols_used=["pay/refund.py",
                                                    "pay/undeclared_api.py"])
        assert report.bypasses == ["pay/undeclared_api.py"]

    def test_stale_clauses_passthrough(self, tree):
        report = check_drift(doc_with(["pay/refund.py*"]), tree,
                             stale_clause_ids=["CON-9"])
        assert report.stale_clauses == ["CON-9"]
        assert not report.clean
