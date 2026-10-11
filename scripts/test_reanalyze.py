#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证「先粗略分类，配好 Key 后升级为精分类」的闭环

场景：用户没填 API Key 就把文件拖进来 → 走规则分类 → 后来配了 Key
     → 点按钮重新分类 → 文件应被 AI 重新命名并挪到新的归档目录。

Usage: python scripts/test_reanalyze.py
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.services.archiver as archiver
from backend.database import get_db, init_db

# 假的 AI 结果：把规则分类「看不出来」的文件精确化
FAKE_AI = {
    "新建 Microsoft Word 文档.docx": {
        "doc_type": "策划案",
        "title": "元旦晚会策划",
        "doc_date": "2025年12月15日",
        "author": "校学生会文艺部",
    },
    "IMG_20250901_143022.jpg": {
        "doc_type": "图片",
        "title": "迎新晚会现场合影",
        "doc_date": "2025年09月01日",
        "author": "",
    },
}

# 模拟「没配 Key」：规则分类
archiver.analyze_file = lambda _path: None


def clean_state():
    """清空上一次运行留下的归档产物和数据库（否则 MD5 去重会拦掉重复文件）。"""
    shutil.rmtree(archiver.OUTPUT_DIR, ignore_errors=True)
    db = Path(archiver.OUTPUT_DIR).parent / "data" / "campusos.db"
    for _ in range(3):
        try:
            if db.exists():
                db.unlink()
            return
        except PermissionError:
            time.sleep(0.3)


def main():
    clean_state()
    init_db()
    tmp = Path(tempfile.mkdtemp(prefix="campusos_reanalyze_"))
    passed = 0
    total = 0

    print(f"{'阶段':<8} {'文件名':<30} {'分类':<8} {'归档名':<44} 结果")
    print("-" * 110)

    for name, ai_result in FAKE_AI.items():
        total += 1
        src = tmp / name
        src.write_text(f"测试内容：{name}", encoding="utf-8")

        # 阶段 1：无 Key，规则分类
        archiver.analyze_file = lambda _path: None
        first = archiver.archive_file(src)
        if not first:
            print(f"{'粗分类':<8} {name:<30} {'(归档失败)':<8}")
            continue
        path_before = Path(first["stored_path"])
        print(f"{'粗分类':<8} {name:<30} {first['doc_type']:<8} {path_before.name:<44} ai_analyzed={first['ai_analyzed']}")

        # 阶段 2：配好 Key，AI 精分类
        archiver.analyze_file = lambda _path, r=ai_result: dict(r)
        updated = archiver.reanalyze_file(first["id"])

        if not updated:
            print(f"{'精分类':<8} {name:<30} (未升级，跳过)")
            continue

        path_after = Path(updated["stored_path"])
        moved = path_after != path_before and path_after.exists() and not path_before.exists()
        marked = updated["ai_analyzed"] == 1
        renamed = path_after.name.startswith(ai_result["doc_date"] + "-" + ai_result["doc_type"])

        ok = moved and marked and renamed
        passed += ok
        detail = "OK" if ok else f"X moved={moved} marked={marked} renamed={renamed}"
        print(f"{'精分类':<8} {name:<30} {updated['doc_type']:<8} {path_after.name:<44} {detail}")

        # 阶段 3：重复调用应被跳过（已精分类的不再处理）
        again = archiver.reanalyze_file(first["id"])
        if again is None:
            print(f"{'重复调用':<8} {name:<30} 已跳过                                  OK")
        else:
            print(f"{'重复调用':<8} {name:<30} X 应该跳过但又被处理了一次")

    print("-" * 110)
    print(f"通过 {passed}/{total}")

    shutil.rmtree(tmp, ignore_errors=True)
    clean_state()
    print("（测试产物已清理）")


if __name__ == "__main__":
    main()
