"""
文件自动归档助手 - 入口

默认启动 Windows 系统托盘模式（无命令行窗口请使用 pythonw main.py）。
命令行模式请运行: python cli.py
"""

import sys


def _show_error_and_exit(message: str) -> None:
    """以对话框或命令行方式显示错误提示。"""
    error_text = f"FileOrganizer 启动失败\n\n{message}\n\n请按任意键退出..."
    try:
        # 优先用对话框
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "FileOrganizer 启动失败", 0x10)
    except Exception:
        pass
    print(error_text, file=sys.stderr)
    input()
    sys.exit(1)


if __name__ == "__main__":
    try:
        from tray_app import run_tray_app
    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else str(e)
        _show_error_and_exit(
            f"缺少必要的依赖库：{missing}\n\n"
            "请先安装依赖：\n"
            "  pip install -r requirements.txt\n\n"
            "如果已安装，请检查 Python 环境是否正确。"
        )
    except Exception as e:
        _show_error_and_exit(f"初始化失败：{e}")

    try:
        run_tray_app()
    except Exception as e:
        _show_error_and_exit(f"程序运行出错：{e}")
