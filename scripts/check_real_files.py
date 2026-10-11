#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拿真实文件夹跑一遍规则分类，看命中率

只读文件名和正文开头，不复制、不移动、不改动任何原文件。

Usage: python scripts/check_real_files.py "C:\\Users\\GHDra\\Desktop\\工作留痕"
"""
import logging
import sys
import warnings
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 读 PDF 时 PyPDF2 会刷一堆解析警告，对使用者没意义
warnings.filterwarnings("ignore")
logging.getLogger("PyPDF2").setLevel(logging.ERROR)

from backend.utils.content_extractor import extract_content_preview
from backend.utils.rule_classifier import classify

# 参与检查的扩展名
EXTS = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".pdf",
        ".txt", ".md", ".jpg", ".jpeg", ".png", ".zip", ".mp4", ".csv"}

# 能从正文里读标题的格式（图片/压缩包没有正文，跳过内容对比）
TEXT_EXTS = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".pdf", ".txt", ".md", ".csv"}


def first_line(file_path: Path) -> str:
    """取正文第一行，作为判断分类对不对的参照"""
    try:
        preview = extract_content_preview(file_path)
    except Exception:
        return ""
    line = preview.title_section.splitlines()[0] if preview.title_section else ""
    # 提取失败时该函数会返回「（文件名为：xxx）」，这种不算有正文
    if line.startswith("（文件名为："):
        return ""
    return line.strip()[:40]


def write_csv(files, root: Path, out: Path) -> None:
    """导出成 CSV，方便用 Excel 打开逐个核对。"""
    import csv

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["相对路径", "文件名", "格式", "规则判定", "置信度",
                    "判定依据", "需要AI", "正文首行（用来核对对不对）"])
        for p in files:
            r = classify(p.name)
            content = first_line(p) if p.suffix.lower() in TEXT_EXTS else ""
            w.writerow([str(p.relative_to(root)), p.name, p.suffix.lower(),
                        r.doc_type,
                        {"high": "确定", "medium": "较确定", "low": "猜不出"}[r.confidence],
                        r.reason, "是" if r.needs_ai else "",
                        content])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    root = Path(sys.argv[1])
    if not root.exists():
        print(f"路径不存在：{root}")
        return

    files = sorted(f for f in root.rglob("*") if f.is_file() and f.suffix.lower() in EXTS)
    if not files:
        print("这个文件夹里没有可检查的文件")
        return

    print(f"扫描目录：{root}")
    print(f"文件总数：{len(files)}\n")

    # 导出核对表，方便在 Excel 里筛「猜不出」的看看到底能不能忍
    csv_path = Path(__file__).resolve().parent.parent / "分类核对表.csv"
    write_csv(files, root, csv_path)
    print(f"已导出核对表：{csv_path}")
    print("  （Excel 打开，按「置信度」列筛选就能看）\n")

    # ── 逐文件分类 ──
    hits = {"high": [], "medium": [], "low": []}
    for f in files:
        r = classify(f.name)
        hits[r.confidence].append((f, r))

    # ── 统计 ──
    total = len(files)
    print("=" * 78)
    print("分类置信度分布")
    print("=" * 78)
    for level, label in (("high", "确定（文种在文件名末尾）"),
                         ("medium", "较确定（命中关键词）"),
                         ("low", "猜不出（需要 AI 读内容）")):
        group = hits[level]
        print(f"  {label:<24} {len(group):>4} 个   {len(group)/total*100:.0f}%")

    print(f"\n  规则能给出具体分类：{len(hits['high'])+len(hits['medium'])}/{total} "
          f"({(len(hits['high'])+len(hits['medium']))/total*100:.0f}%)")
    print(f"  需要 AI 补的：{len(hits['low'])}/{total} ({len(hits['low'])/total*100:.0f}%)")

    # ── 分类结果分布 ──
    print("\n" + "=" * 78)
    print("落在哪些分类")
    print("=" * 78)
    for doc_type, n in Counter(r.doc_type for _, r in hits["high"] + hits["medium"]).most_common():
        print(f"  {doc_type:<10} {n:>4}")

    # ── 明细：文件名 → 分类 | 正文首行（用于人工核对对错）──
    print("\n" + "=" * 78)
    print("明细核对表（正文首行 = 文件里真正的标题，用来判断分得对不对）")
    print("=" * 78)
    for level, title in (("high", "【确定】"), ("medium", "【较确定】"), ("low", "【猜不出 / 需要 AI】")):
        if not hits[level]:
            continue
        print(f"\n{title} {len(hits[level])} 个")
        print("-" * 78)
        for f, r in hits[level]:
            content = first_line(f) if f.suffix.lower() in TEXT_EXTS else ""
            rel = f.relative_to(root)
            print(f"  {rel}")
            print(f"      规则判定：{r.doc_type}   ({r.reason})")
            if content:
                print(f"      正文首行：{content}")
            print()

    # 需要 AI 的文件单独列一份，方便判断"AI 到底有没有用"
    lows = hits["low"]
    if lows:
        print("\n" + "=" * 78)
        print(f"只靠文件名猜不出来的 {len(lows)} 个（这些是 AI 的价值所在）")
        print("=" * 78)
        for f, _ in lows:
            print(f"  {f.relative_to(root)}")


if __name__ == "__main__":
    main()
