#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端验证：未配置 AI Key 时的归档分类效果

模拟「用户没填 Key 就拖文件进来」，检查文件被分到哪、叫什么名字。

Usage: python scripts/test_archive_rules.py
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.services.archiver as archiver
from backend.database import init_db

# 强制走规则路径（模拟未配置 Key）
archiver.analyze_file = lambda _path: None

CASES = [
    ("关于举办2026年元旦晚会的通知.docx", "通知"),
    ("2025年迎新晚会活动策划书.docx", "策划案"),
    ("学生会第3次例会纪要.docx", "会议纪要"),
    ("迎新晚会经费预算.xlsx", "预算表"),
    ("元旦晚会签到表.xlsx", "签到表"),
    ("团委学生干部通讯录.xlsx", "通讯录"),
    ("参赛人员名单.docx", "统计表"),
    ("10月值班表.xlsx", "排班表"),
    ("2025级新生报名表.docx", "收集表"),
    ("张三一个人简历.pdf", "简历"),
    ("IMG_20250901_143022.jpg", "图片"),
    ("元旦晚会现场.mp4", "视频"),
    ("历届活动资料.zip", "压缩包"),
    ("新建 Microsoft Word 文档.docx", "Word文档"),
]


def clean_state():
    """清空上一次运行留下的归档产物和数据库。

    必须在开头调用：残留的数据库会让 MD5 去重把测试文件全部当成重复丢弃。
    """
    shutil.rmtree(archiver.OUTPUT_DIR, ignore_errors=True)
    db = Path(archiver.OUTPUT_DIR).parent / "data" / "campusos.db"
    for _ in range(3):
        try:
            if db.exists():
                db.unlink()
            return
        except PermissionError:
            time.sleep(0.3)  # Windows 文件句柄延迟释放


def main():
    clean_state()
    init_db()
    tmp = Path(tempfile.mkdtemp(prefix="campusos_test_"))
    passed = 0

    print(f"{'文件名':<34} {'分类结果':<10} {'归档子目录':<14} 结果")
    print("-" * 90)

    for name, expected in CASES:
        src = tmp / name
        # 每个文件写入不同内容，避免被内容去重逻辑拦截
        src.write_text(f"测试内容：{name}", encoding="utf-8")
        result = archiver.archive_file(src)

        if not result:
            print(f"{name:<34} {'(归档失败)':<10}")
            continue

        ok = result["doc_type"] == expected
        if ok:
            passed += 1

        # 从归档路径里取出子目录，验证归类是否符合预期
        rel = Path(result["stored_path"]).relative_to(archiver.OUTPUT_DIR)
        subdir = str(rel.parent).replace("未分类", "").strip("\\/") or "-"
        mark = "OK" if ok else f"X 期望:{expected}"

        short = name if len(name) <= 32 else name[:30] + ".."
        print(f"{short:<34} {result['doc_type']:<10} {subdir:<14} {mark}")

    print("-" * 90)
    print(f"通过 {passed}/{len(CASES)}")

    shutil.rmtree(tmp, ignore_errors=True)
    clean_state()
    print("（测试产物已清理）")


if __name__ == "__main__":
    main()
