# -*- coding: utf-8 -*-
"""
组装 CampusOS 发布包

产出（在 release/ 下）：
    CampusOS-v{VER}.zip         免安装版
    CampusOS-Setup-v{VER}.exe   NSIS 安装向导（需另跑 makensis）

前置：先跑 PyInstaller 生成 dist/CampusOS.exe

设计要点（吸取 2026-10-11 的教训）：
  - **不删除 release/CampusOS 目录**，改为逐文件覆盖，
    因为该目录不受 git 跟踪（release/ 已 gitignore），删了就找不回。
  - 所有文本文件统一 UTF-8 无 BOM + CRLF（Windows 记事本友好）。
  - 组装后自动复核：版本号、敏感文件、exe 大小。

用法：
    python scripts/build_release.py            # 只组装
    python scripts/build_release.py 0.1.3      # 指定版本号
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / "release"
DIST_EXE = ROOT / "dist" / "CampusOS.exe"
APP_DIR = RELEASE / "CampusOS"


def read_version() -> str:
    src = (ROOT / "backend" / "version.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', src)
    if not m:
        raise SystemExit("错误: backend/version.py 里找不到 __version__")
    return m.group(1)


def write_crlf_utf8(path: Path, text: str, bom: bool = False) -> None:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)


def main() -> int:
    ver = sys.argv[1] if len(sys.argv) > 1 else read_version()
    print(f"版本号: {ver}")

    if not DIST_EXE.exists():
        print(f"错误: 找不到 {DIST_EXE}，请先跑 PyInstaller")
        return 1

    # ── 1. 目录（存在则复用，不删） ──
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "config").mkdir(exist_ok=True)
    (APP_DIR / "input").mkdir(exist_ok=True)

    # ── 2. 主程序 ──
    shutil.copy2(DIST_EXE, APP_DIR / "CampusOS.exe")
    size_mb = (APP_DIR / "CampusOS.exe").stat().st_size / 1024 / 1024
    print(f"  exe: {size_mb:.1f} MB")

    # ── 3. 空白配置模板（只放 example，绝不放真实 settings.json） ──
    example = ROOT / "config" / "settings.example.json"
    shutil.copy2(example, APP_DIR / "config" / "settings.example.json")
    import json

    cfg = json.loads(example.read_text(encoding="utf-8"))
    keys = cfg.get("AI_API_KEYS", {})
    if any(v for v in keys.values()):
        print("  错误: settings.example.json 里含非空 API Key，已中止")
        return 1
    print("  配置模板: 密钥为空 ✓")

    # ── 4. 使用指南版本号（保持原编码风格，统一 CRLF） ──
    guide = APP_DIR / "使用指南.txt"
    if guide.exists():
        text = guide.read_text(encoding="utf-8")
        new, n = re.subn(r"v\d+\.\d+\.\d+", f"v{ver}", text)
        write_crlf_utf8(guide, new)
        print(f"  使用指南: 版本号替换 {n} 处")
    else:
        print("  警告: 使用指南.txt 不存在")

    # ── 5. setup.bat 规范化（版本号 + CRLF） ──
    bat = APP_DIR / "setup.bat"
    if bat.exists():
        text = bat.read_text(encoding="utf-8")
        text, n = re.subn(r"v\d+\.\d+\.\d+", f"v{ver}", text)
        write_crlf_utf8(bat, text)
        raw = bat.read_bytes()
        lf, crlf = raw.count(b"\n"), raw.count(b"\r\n")
        ok = lf == crlf and lf > 0 and raw[:3] != b"\xef\xbb\xbf"
        print(f"  setup.bat: 版本号替换 {n} 处, CRLF {crlf}/{lf} {'✓' if ok else '✗ 行尾异常'}")
    else:
        print("  警告: setup.bat 不存在")

    # ── 6. 打 zip（在 release/ 下，保持 CampusOS/ 顶层目录） ──
    zip_path = RELEASE / f"CampusOS-v{ver}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for item in sorted(APP_DIR.rglob("*")):
            rel = item.relative_to(RELEASE)
            if item.is_dir():
                z.writestr(str(rel).replace("\\", "/") + "/", "")
            else:
                z.write(item, str(rel).replace("\\", "/"))
    print(f"  zip: {zip_path.name}  {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

    # ── 7. NSIS 需要的 setup.nsi 版本号 ──
    # 注意：setup.nsi 含非 ASCII 字符（── 装饰线），而 makensis 按系统 ANSI
    # 代码页读取脚本，UTF-8 无 BOM 会报 "Bad text encoding" 并中止。
    # 必须写成 **UTF-8 带 BOM**，makensis 才会认出编码。
    nsi = RELEASE / "setup.nsi"
    if nsi.exists():
        text = nsi.read_text(encoding="utf-8-sig")
        text, n = re.subn(r'!define VERSION "[\d.]+"', f'!define VERSION "{ver}"', text)
        write_crlf_utf8(nsi, text, bom=True)
        print(f"  setup.nsi: VERSION={ver}, UTF-8 BOM 已加 (替换 {n} 处)")

    # ── 8. 复核 ──
    print("\n复核:")
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        leaked = [n for n in names if re.search(r"settings\.json$|\.db$|campusos\.log", n)]
        exe_entry = [n for n in names if n.endswith("CampusOS.exe")]
        print(f"  zip 条目数: {len(names)}")
        for n in names:
            info = z.getinfo(n)
            if info.file_size:
                print(f"    {n}  ({info.file_size / 1024:.0f} KB)")
            else:
                print(f"    {n}")
        print(f"  敏感文件: {'⚠ ' + str(leaked) if leaked else '无 ✓'}")
        print(f"  含 exe: {'✓' if exe_entry else '✗'}")
        return 0 if (not leaked and exe_entry) else 1


if __name__ == "__main__":
    sys.exit(main())
