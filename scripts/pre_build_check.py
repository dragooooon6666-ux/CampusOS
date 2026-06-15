#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
# Force UTF-8 on Windows to avoid encoding errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

"""CampusOS 打包前密钥泄露检查

检查项：
1. 源代码中是否包含 API Key（sk-*, ghp_*, etc.）
2. 打包配置是否排除了敏感文件
3. 示例配置文件是否干净

Usage: python scripts/pre_build_check.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS = 0
WARNINGS = 0

# ── 敏感模式 ──
# DeepSeek, OpenAI, Anthropic, 其他 OpenAI 兼容 Key
API_KEY_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,60}', "OpenAI 兼容 API Key (sk-xxx)"),
    (r'ghp_[a-zA-Z0-9]{30,50}', "GitHub Personal Access Token"),
    (r'gho_[a-zA-Z0-9]{30,50}', "GitHub OAuth Token"),
    (r'xai-[a-zA-Z0-9]{20,60}', "xAI API Key"),
    (r'[a-zA-Z0-9]{32,64}', "疑似长随机字符串（可能是 Key）"),
]

# ── 不应包含 Key 的文件/目录 ──
SCAN_DIRS = ["frontend", "backend", "scripts", "launcher.py", "CampusOS.spec", "release/setup.nsi"]
# 这些文件允许包含示例/占位 Key
KEY_WHITELIST = [
    "settings.example.json",   # 空白模板
    "DEVELOPMENT_LOG.md",      # 开发日志可能提到 Key 格式
    "pre_build_check.py",      # 检查脚本自身的 Key 模式
]

def error(path, msg):
    global ERRORS
    ERRORS += 1
    rel = os.path.relpath(path, ROOT)
    print(f"  [ERROR] {rel}: {msg}")

def warning(path, msg):
    global WARNINGS
    WARNINGS += 1
    rel = os.path.relpath(path, ROOT)
    print(f"  [WARN] {rel}: {msg}")


def scan_file(filepath):
    """扫描单个文件中的敏感字符串"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return

    rel = os.path.relpath(filepath, ROOT)
    filename = os.path.basename(filepath)

    # 跳过白名单文件
    for wl in KEY_WHITELIST:
        if wl in rel:
            return

    for pattern, desc in API_KEY_PATTERNS:
        matches = re.findall(pattern, content)
        # 过滤掉明显的非 Key 字符串（如 base64 license key 占位）
        for m in matches:
            # 跳过占位符/示例
            if m.lower() in ("sk-your-api-key-here", "sk-xxx", "sk-example",
                            "ghp_example", "ghp_xxxxxxxxxxxx"):
                continue
            if "example" in m.lower() or "placeholder" in m.lower():
                continue
            # 全相同字符 → 不是 Key
            if len(set(m)) < 4:
                continue
            error(filepath, f"Found {desc}: {m[:8]}...{m[-4:]}")


def check_example_config():
    """检查示例配置是否干净"""
    example = ROOT / "config" / "settings.example.json"
    if not example.exists():
        error(example, "settings.example.json 不存在")
        return

    import json
    with open(example, encoding="utf-8") as f:
        data = json.load(f)

    keys = data.get("AI_API_KEYS", {})
    for provider, key in keys.items():
        if key.strip():
            error(example, f"settings.example.json 中包含 {provider} 的 API Key！必须为空字符串")


def check_gitignore():
    """检查敏感文件是否被 gitignore"""
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        error(gitignore, ".gitignore 不存在")
        return

    with open(gitignore, encoding="utf-8") as f:
        content = f.read()

    must_ignore = [
        "config/settings.json",
    ]
    for item in must_ignore:
        if item not in content:
            error(gitignore, f".gitignore 缺少: {item}")


def check_pyinstaller_spec():
    """检查 PyInstaller 配置"""
    spec = ROOT / "CampusOS.spec"
    if not spec.exists():
        error(spec, "CampusOS.spec 不存在")
        return

    with open(spec, encoding="utf-8") as f:
        content = f.read()

    # 不应该直接打包 settings.json
    if "('config', 'config')" in content or "'config/settings.json'" in content:
        if "settings.json" in content and "settings.example.json" not in content:
            error(spec, "CampusOS.spec 可能直接打包了 settings.json（含 Key）")


def main():
    print("=" * 50)
    print("CampusOS 打包前安全检查")
    print("=" * 50)

    # 1. 扫描源代码
    print("\n[1] 扫描源代码中的密钥...")
    for item in SCAN_DIRS:
        full = ROOT / item
        if full.is_file():
            scan_file(full)
        elif full.exists():
            for dirpath, _, filenames in os.walk(full):
                for fn in filenames:
                    if fn.endswith((".py", ".js", ".json", ".html", ".css", ".bat", ".nsi", ".spec")):
                        scan_file(os.path.join(dirpath, fn))
        else:
            warning(item, "目录不存在，跳过")

    # 2. 检查示例配置
    print("\n[2] 检查示例配置...")
    check_example_config()

    # 3. 检查 gitignore
    print("\n[3] 检查 .gitignore...")
    check_gitignore()

    # 4. 检查 PyInstaller spec
    print("\n[4] 检查打包配置...")
    check_pyinstaller_spec()

    # ── 结果 ──
    print("\n" + "=" * 50)
    if ERRORS:
        print(f"FAIL: {ERRORS} errors, {WARNINGS} warnings -- DO NOT BUILD!")
        sys.exit(1)
    elif WARNINGS:
        print(f"PASS: no errors, {WARNINGS} warnings -- OK to build")
    else:
        print("PASS: all checks passed -- safe to build")
    sys.exit(0)


if __name__ == "__main__":
    main()
