"""
运行时路径解析 — 兼容开发环境与 PyInstaller 打包环境

用户数据（数据库、归档输出、input 暂存）必须存放在 exe 所在目录，
否则会被 PyInstaller 解压到系统临时目录，程序退出后数据丢失。

开发时：项目根目录
打包后：exe 所在目录
"""

import sys
from pathlib import Path


def get_base_dir() -> Path:
    """返回用户数据的存放目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
