#!/usr/bin/env python3
"""校验 CAPABILITY_MAP.md 中 路径:行号 证据引用的正确性。

用法: python3 scripts/verify_refs.py  （需先检出全部 submodule）
输出: 每条引用的存在性/行号范围校验结果，明细写入 scripts/verify_result.json
"""
import re
import os
import sys
import json
from collections import defaultdict

DOC = os.path.join(os.path.dirname(__file__), "..", "CAPABILITY_MAP.md")
ROOT = os.path.join(os.path.dirname(__file__), "..")

SUBMODULES = [
    "jiuwenswarm", "agent-core", "agent-studio", "deepsearch", "agent-runtime",
    "jiuwensymbiosis", "agent-memory", "skillhub", "agent-tools", "agent-protocol", "relay",
]
SUB_RE = "|".join(SUBMODULES)
REF_RE = re.compile(
    r"`((?:" + SUB_RE + r")/[^`\s]+?):(L\d+(?:-L\d+)?(?:[、,]\s*L\d+(?:-L\d+)?)*)`"
)


def parse_line_range(spec):
    """把 L12-L34、L12 等解析为 [(start,end),...]"""
    ranges = []
    for part in re.split(r"[、,]\s*", spec):
        m = re.match(r"L(\d+)(?:-L?(\d+))?", part)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else start
            ranges.append((start, end))
    return ranges


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return -1


def check_keys(lines):
    """对配置表格行做内容级校验：引用行号处（±3 行内）是否出现该配置键。"""
    row_re = re.compile(r"^\|(.+)\|(?:.*)$")
    hard_miss, drift = [], []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s.startswith("|"):
            continue
        for m in REF_RE.finditer(line):
            rel_path, spec = m.group(1), m.group(2)
            # 第一列的键名
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells:
                continue
            key_cell = cells[0]
            tokens = re.findall(r"`([^`]+)`", key_cell)
            if not tokens:
                tokens = [t.strip() for t in re.split(r"[/、]", key_cell) if t.strip()]
            toks = set()
            for t in tokens:
                for seg in re.split(r"[.\s]+", t):
                    seg = seg.strip("`-")
                    if len(seg) >= 4 and re.search(r"[A-Za-z]", seg):
                        toks.add(seg.lower())
            if not toks:
                continue
            abs_path = os.path.normpath(os.path.join(ROOT, rel_path))
            if not os.path.isfile(abs_path):
                continue  # 存在性由主流程负责
            flines = open(abs_path, encoding="utf-8", errors="replace").readlines()
            ranges = parse_line_range(spec)
            for start, end in ranges:
                exact = "".join(flines[max(0, start - 1):end]).lower()
                near = "".join(flines[max(0, start - 4):min(len(flines), end + 3)]).lower()
                if any(t in exact for t in toks):
                    continue
                if any(t in near for t in toks):
                    drift.append((i, rel_path, f"L{start}-L{end}", sorted(toks)))
                else:
                    hard_miss.append((i, rel_path, f"L{start}-L{end}", sorted(toks)))
    return hard_miss, drift


def main():
    with open(DOC, encoding="utf-8") as f:
        lines = f.readlines()

    if "--keys" in sys.argv:
        hard, drift = check_keys(lines)
        print(f"配置表内容校验：疑似偏移 {len(drift)} 条，完全不符 {len(hard)} 条")
        print("\n--- 疑似偏移（±3 行内可找到键名）---")
        for i, p, r, t in drift:
            print(f"  L{i} {p}:{r} keys={t}")
        print("\n--- 完全不符（±3 行内也找不到键名）---")
        for i, p, r, t in hard:
            print(f"  L{i} {p}:{r} keys={t}")
        return

    results = []
    by_status = defaultdict(list)
    seen = set()

    for i, line in enumerate(lines, 1):
        for m in REF_RE.finditer(line):
            rel_path, spec = m.group(1), m.group(2)
            abs_path = os.path.normpath(os.path.join(ROOT, rel_path))
            if not os.path.isfile(abs_path):
                status, detail = "MISSING_FILE", "文件不存在"
            else:
                n = count_lines(abs_path)
                ranges = parse_line_range(spec)
                bad = [r for r in ranges if r[0] > n or r[1] > n]
                if bad:
                    status, detail = "OUT_OF_RANGE", f"文件仅 {n} 行，越界引用 {bad}"
                else:
                    status, detail = "OK", f"{n} 行"
            results.append((i, rel_path, spec, status, detail))
            by_status[status].append((i, rel_path, spec, detail))
            seen.add((rel_path, spec))

    total = len(results)
    print(f"总引用条目: {total}（唯一 {len(seen)}）")
    for status in ("OK", "MISSING_FILE", "OUT_OF_RANGE"):
        print(f"{status}: {len(by_status[status])}")

    out = {"total": total, "unique": len(seen),
           "missing": [r[:3] for r in by_status["MISSING_FILE"]],
           "out_of_range": [(r[0], r[1], r[2], r[4]) for r in by_status["OUT_OF_RANGE"]]}
    out_path = os.path.join(os.path.dirname(__file__), "verify_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"明细已写入 {out_path}")


if __name__ == "__main__":
    main()
