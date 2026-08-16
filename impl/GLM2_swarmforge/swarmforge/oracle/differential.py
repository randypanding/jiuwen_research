"""差分测试引擎（H5）：行为指纹、差分判定、黄金输出比对。

设计要点（r3-golden-output 与差分测试研究结论的工程化）：
- 引擎与执行解耦：输入是"执行轨迹"（instance_id -> input_id -> observed），
  执行本身发生在沙箱/工作树中，引擎是纯比较逻辑，可离线测试。
- 先控制非确定性再差分：normalizer 剥离时间戳/uuid/随机 id 等字段（配置化）；
  剥离后仍发散的差异才是行为差异。
- 差异必须被解释（INV9）：落在已登记 don't-care 维度内的差异 = 合法自由度；
  未覆盖的差异 = DIFFERENCE_FOUND（spec 沉默事件）；扰动复跑后差异位置不稳定
  = INCONCLUSIVE（进入统计通道）。
- 黄金比对四层门（R3）：manifest 一致性 → 字节级精确比对；manifest 不一致
  直接 INCONCLUSIVE（比对无效，不能据此放行或阻断）。
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Optional

from .schema import DiffConclusion, DifferentialReport, GoldenManifest
from ..specrepo.schema import DontCareEntry


class OutputNormalizer:
    """输出规范化：把可观察输出变成规范化字符串再比较。

    config:
      drop_keys: 需剥离的键名（如 timestamp/nonce/session_id）
      redact_patterns: 需替换为 <REDACTED> 的正则
    """

    def __init__(self, drop_keys: Optional[set[str]] = None,
                 redact_patterns: Optional[list[str]] = None):
        self.drop_keys = drop_keys or set()
        self.redact_patterns = [re.compile(p) for p in (redact_patterns or [])]

    def normalize(self, observed) -> str:
        if not isinstance(observed, (dict, list)):
            observed = {"value": observed}
        cleaned = self._clean(observed)
        canon = json.dumps(cleaned, ensure_ascii=False, sort_keys=True)
        for pat in self.redact_patterns:
            canon = pat.sub("<REDACTED>", canon)
        return canon

    def _clean(self, obj):
        if isinstance(obj, dict):
            return {
                k: self._clean(v)
                for k, v in obj.items()
                if k not in self.drop_keys
            }
        if isinstance(obj, list):
            return [self._clean(x) for x in obj]
        if isinstance(obj, float):
            return round(obj, 9)  # 消除浮点尾噪（显式约定，非隐藏容差）
        return obj

    def config_hash(self) -> str:
        cfg = json.dumps({
            "drop_keys": sorted(self.drop_keys),
            "redact_patterns": [p.pattern for p in self.redact_patterns],
        }, sort_keys=True)
        return hashlib.sha256(cfg.encode()).hexdigest()


class DiffInputGenerator:
    """确定性差分输入生成器。

    以 (scenario_stimulus, seed) 为根，用 stdlib 确定性 PRNG 生成扰动输入。
    显式 seed 保证可复现——黄金 manifest 锁 seed 的物理基础。
    """

    def __init__(self, seed: int):
        self.seed = seed

    def perturb(self, stimulus: dict, n: int) -> list[dict]:
        import random
        rng = random.Random(self.seed)
        out = []
        for i in range(n):
            item = json.loads(json.dumps(stimulus))  # deep copy
            for key, val in item.items():
                if isinstance(val, int):
                    item[key] = val + rng.randint(-3, 3)
                elif isinstance(val, str):
                    item[key] = val + rng.choice(["", " ", "_x", str(rng.randint(0, 9))])
                elif isinstance(val, list) and val:
                    k = rng.randint(0, len(val) - 1)
                    item[key] = val[:k] + val[k + 1:] if rng.random() < 0.5 else val + [val[0]]
            out.append(item)
        return out

    def input_id(self, stimulus: dict, index: int) -> str:
        blob = json.dumps(stimulus, ensure_ascii=False, sort_keys=True).encode()
        return f"DI-{hashlib.sha256(blob).hexdigest()[:10]}-{index:03d}"


@dataclass
class Divergence:
    input_id: str
    field_path: str
    values: dict[str, str]  # instance_id -> normalized value snippet

    def covered_by(self, dont_cares: list[DontCareEntry]) -> bool:
        """差异是否落在已登记的自由度内。

        dimension 是 glob，可匹配：input_id、字段路径、或 "<input_id>.<字段路径>"。
        例："*.receipt_no" 匹配任意输入下的 receipt_no 字段差异。
        """
        import fnmatch
        full = f"{self.input_id}.{self.field_path}"
        for dc in dont_cares:
            if (fnmatch.fnmatch(self.input_id, dc.dimension)
                    or fnmatch.fnmatch(self.field_path, dc.dimension)
                    or fnmatch.fnmatch(full, dc.dimension)):
                return True
        return False


class DifferentialEngine:
    """实例间行为差分：指纹 → 发散检测 → don't-care 归约 → 扰动复判。"""

    def __init__(self, normalizer: Optional[OutputNormalizer] = None):
        self.normalizer = normalizer or OutputNormalizer()

    def fingerprint(self, traces: dict[str, object]) -> str:
        """instance 的行为指纹：全部输入上规范化输出序列的哈希。"""
        parts = [
            f"{input_id}::{self.normalizer.normalize(obs)}"
            for input_id, obs in sorted(traces.items())
        ]
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()

    def divergences(self, traces_a: dict[str, object],
                    traces_b: dict[str, object]) -> list[Divergence]:
        divs: list[Divergence] = []
        for input_id in sorted(set(traces_a) | set(traces_b)):
            a = traces_a.get(input_id)
            b = traces_b.get(input_id)
            if a is None or b is None:
                divs.append(Divergence(input_id, "<missing>",
                                       {"A": str(a)[:80], "B": str(b)[:80]}))
                continue
            na = self.normalizer.normalize(a)
            nb = self.normalizer.normalize(b)
            if na != nb:
                ja = json.loads(na) if na.startswith(("{", "[")) else {"out": na}
                jb = json.loads(nb) if nb.startswith(("{", "[")) else {"out": nb}
                for path, va, vb in self._first_diff_paths(ja, jb):
                    divs.append(Divergence(input_id, path,
                                           {"A": str(va)[:80], "B": str(vb)[:80]}))
        return divs

    @staticmethod
    def _first_diff_paths(a, b, prefix: str = "") -> list[tuple[str, object, object]]:
        out: list[tuple[str, object, object]] = []
        if type(a) is not type(b):
            return [(prefix or "<root>", a, b)]
        if isinstance(a, dict):
            for k in sorted(set(a) | set(b)):
                out.extend(DifferentialEngine._first_diff_paths(
                    a.get(k), b.get(k), f"{prefix}.{k}" if prefix else k))
        elif isinstance(a, list):
            if len(a) != len(b):
                out.append((f"{prefix}.len", len(a), len(b)))
            for i, (xa, xb) in enumerate(zip(a, b)):
                out.extend(DifferentialEngine._first_diff_paths(
                    xa, xb, f"{prefix}[{i}]"))
        elif a != b:
            out.append((prefix or "<root>", a, b))
        return out[:5]  # 每个输入最多报 5 处，防爆量

    def compare(self, wave_id: str, spec_delta_id: str,
                instance_traces: dict[str, dict[str, object]],
                inputs_used: list[str],
                dont_cares: list[DontCareEntry],
                probe_traces: Optional[dict[str, dict[str, object]]] = None,
                ) -> DifferentialReport:
        """主入口。

        instance_traces: instance_id -> {input_id: observed}
        probe_traces:    扰动复跑（换 seed）后的同构轨迹；差异集不稳定 → INCONCLUSIVE
        """
        ids = sorted(instance_traces)
        fps = {iid: self.fingerprint(instance_traces[iid]) for iid in ids}
        all_divs: list[Divergence] = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                all_divs.extend(self.divergences(instance_traces[ids[i]], instance_traces[ids[j]]))

        report = DifferentialReport(
            wave_id=wave_id, spec_delta_id=spec_delta_id,
            instance_ids=ids, inputs_used=inputs_used, fingerprints=fps,
        )

        if not all_divs:
            report.conclusion = DiffConclusion.EQUIVALENT
            return report

        uncovered = [d for d in all_divs if not d.covered_by(dont_cares)]
        if not uncovered:
            # 全部差异都落在显式自由度内：合法非确定性，不算沉默
            report.conclusion = DiffConclusion.EQUIVALENT
            report.detail = f"{len(all_divs)} divergences all within registered don't-care zones"
            return report

        # 扰动复判：差异在换 seed 后消失/移位 → 非确定性嫌疑，进统计通道
        if probe_traces is not None:
            probe_divs: list[Divergence] = []
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    probe_divs.extend(self.divergences(probe_traces[ids[i]], probe_traces[ids[j]]))
            main_set = {(d.input_id, d.field_path) for d in uncovered}
            probe_set = {(d.input_id, d.field_path) for d in probe_divs}
            if main_set != probe_set:
                report.conclusion = DiffConclusion.INCONCLUSIVE
                report.nondet_suspects = sorted(str(x) for x in (main_set ^ probe_set))
                report.detail = "divergence set unstable under perturbation rerun"
                return report

        report.conclusion = DiffConclusion.DIFFERENCE_FOUND
        report.divergent_inputs = sorted({d.input_id for d in uncovered})
        report.detail = "; ".join(
            f"{d.input_id}@{d.field_path}: {d.values}" for d in uncovered[:5]
        )
        return report


class GoldenGate:
    """R3 黄金输出门：L0 manifest 一致性 + L1 字节级比对。"""

    @staticmethod
    def verify_manifest(manifest: GoldenManifest, code_hash: str, deps_hash: str,
                        seed: int, normalizer_config_hash: str) -> tuple[bool, str]:
        """L0：环境指纹不一致 → 比对无效（INCONCLUSIVE），不得据黄金结果放行/阻断。"""
        checks = [
            (manifest.code_hash == code_hash, "code_hash mismatch"),
            (manifest.deps_hash == deps_hash, "deps_hash mismatch"),
            (manifest.seed == seed, "seed mismatch"),
            (manifest.normalizer_config_hash == normalizer_config_hash,
             "normalizer_config mismatch"),
        ]
        failed = [msg for ok, msg in checks if not ok]
        if failed:
            return False, "; ".join(failed)
        return True, "manifest consistent"

    @staticmethod
    def compare(golden_bytes: bytes, observed_bytes: bytes) -> tuple[str, str]:
        """L1：字节级精确比对（逐行敏感制品不做任何容差）。"""
        if golden_bytes == observed_bytes:
            return "pass", "byte-identical"
        return "fail", (
            f"byte mismatch: golden={len(golden_bytes)}B observed={len(observed_bytes)}B"
        )
