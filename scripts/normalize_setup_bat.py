# -*- coding: utf-8 -*-
"""
规范化 release/CampusOS/setup.bat：版本号 + 行尾

为什么需要这个脚本
------------------
cmd.exe 解析批处理文件时，遇到 **LF 换行** 会吃掉含多字节字符行的行首，
报 "'xx系统' 不是内部或外部命令"。该文件原本正是 UTF-8 + LF，随
v0.1.0 / v0.1.2 分发出去时是坏的（实测 5 处报错）。

实测矩阵（2026-10-11，cmd.exe / 代码页 936）：
    UTF-8 + LF    -> 6 处报错   ← 原状
    GBK   + CRLF  -> 8 处报错   ← 更糟，勿用
    UTF-8 + CRLF  -> 0 处报错   ← 正确组合

结论：真正的元凶是**行尾**，不是编码。保持 UTF-8（配合文件内 chcp 65001），
把行尾改成 CRLF 即可。**切勿转成 GBK。**

用法：python scripts/normalize_setup_bat.py [版本号]
      不给版本号则沿用文件里现有的，只修行尾。
幂等：可重复运行。
"""
import re
import sys
from pathlib import Path

BAT = Path(__file__).resolve().parent.parent / "release" / "CampusOS" / "setup.bat"
VER_RE = re.compile(r"v(\d+\.\d+\.\d+)")


def main() -> int:
    if not BAT.exists():
        print(f"错误: 找不到 {BAT}")
        return 1

    raw = BAT.read_bytes()
    before_crlf = raw.count(b"\r\n")
    before_lf = raw.count(b"\n")
    before_bom = raw[:3] == b"\xef\xbb\xbf"

    text = raw.decode("utf-8")

    # 1. 版本号（可选）
    if len(sys.argv) > 1:
        new_ver = sys.argv[1].lstrip("v")
        found = VER_RE.search(text)
        if not found:
            print("错误: 文件里找不到形如 v0.1.0 的版本号，未改动")
            return 1
        old_ver = found.group(0)
        if old_ver != f"v{new_ver}":
            text = VER_RE.sub(f"v{new_ver}", text)
            print(f"版本号: {old_ver} -> v{new_ver}")
        else:
            print(f"版本号: 已是 v{new_ver}，无需改动")
    else:
        found = VER_RE.search(text)
        print(f"版本号: 未指定，沿用 {found.group(0) if found else '(未找到)'}")

    # 2. 行长统一为 CRLF
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")

    # 3. UTF-8 无 BOM 写回
    BAT.write_bytes(text.encode("utf-8"))

    # 4. 复核
    after = BAT.read_bytes()
    n_lf = after.count(b"\n")
    n_crlf = after.count(b"\r\n")
    has_bom = after[:3] == b"\xef\xbb\xbf"

    print(
        f"行尾: 改前 LF={before_lf}/CRLF={before_crlf} -> "
        f"改后 LF={n_lf}/CRLF={n_crlf}"
    )
    print(f"BOM : {'有 (异常!)' if before_bom else '无'} -> {'有 (异常!)' if has_bom else '无 (正确)'}")
    print(f"大小: {len(raw)} -> {len(after)} 字节")

    ok = (n_lf == n_crlf) and not has_bom and n_lf > 0
    print("复核: " + ("全部通过 ✓" if ok else "未通过 ✗"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
