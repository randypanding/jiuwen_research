#!/usr/bin/env python3
"""抽样输出 CAPABILITY_MAP.md 证据引用的 实际代码内容，用于人工比对描述准确性。

用法: python3 scripts/sample_refs.py [每组件抽样数，默认3]
"""
import re
import os
import sys
import random

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
    ranges = []
    for part in re.split(r"[、,]\s*", spec):
        m = re.match(r"L(\d+)(?:-L?(\d+))?", part)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else start
            ranges.append((start, end))
    return ranges


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    random.seed(42)
    with open(DOC, encoding="utf-8") as f:
        lines = f.readlines()

    # 收集 (doc_line, context_desc, path, first_range)
    entries = []
    for i, line in enumerate(lines):
        for m in REF_RE.finditer(line):
            rel_path, spec = m.group(1), m.group(2)
            ranges = parse_line_range(spec)
            if not ranges:
                continue
            # 向上找最近的描述行（非证据行的 bullet/文本）
            ctx = ""
            j = i - 1
            while j >= 0:
                s = lines[j].strip()
                if s and not s.startswith("证据") and "证据:" not in s:
                    ctx = s
                    break
                j -= 1
            entries.append((i, ctx, rel_path, ranges[0]))

    # 按子模块分组抽样
    by_sub = {}
    for e in entries:
        by_sub.setdefault(e[2].split("/")[0], []).append(e)

    out = []
    for sub in sorted(by_sub):
        pool = by_sub[sub]
        sample = random.sample(pool, min(n_per, len(pool)))
        out.append(f"\n{'='*80}\n### {sub}（共 {len(pool)} 条，抽样 {len(sample)}）\n{'='*80}")
        for doc_line, ctx, rel_path, (start, end) in sorted(sample):
            abs_path = os.path.normpath(os.path.join(ROOT, rel_path))
            out.append(f"\n--- 文档第 {doc_line} 行 ---")
            out.append(f"描述: {ctx[:200]}")
            out.append(f"引用: {rel_path}:{'L%d-L%d' % (start, end) if start != end else 'L%d' % start}")
            try:
                with open(abs_path, encoding="utf-8", errors="replace") as f:
                    flines = f.readlines()
                show_end = min(end, start + 14)  # 最多展示15行
                for k in range(start - 1, min(show_end, len(flines))):
                    out.append(f"  {k+1:>5}| {flines[k].rstrip()}")
            except OSError as ex:
                out.append(f"  读取失败: {ex}")

    report = "\n".join(out)
    path = os.path.join(os.path.dirname(__file__), "sample_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"抽样报告已写入 {path}（{sum(len(v) for v in by_sub.values())} 条总样本池）")


if __name__ == "__main__":
    main()
