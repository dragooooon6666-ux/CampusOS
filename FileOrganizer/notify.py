"""
用户通知模块

提供三类用户可见的通知：
1. 错误弹窗（messagebox）— 替代静默日志
2. 托盘气泡通知 — 归档完成反馈
3. 首次使用引导窗口
"""

import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# ── 错误弹窗（线程安全）───────────────────────────────────

# 记录本会话已弹过的错误类型，避免重复刷屏
_shown_errors: set[str] = set()


def _show_messagebox(title: str, message: str, msg_type: str = "warning"):
    """线程安全地弹出 messagebox。"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        if msg_type == "error":
            messagebox.showerror(title, message, parent=root)
        elif msg_type == "info":
            messagebox.showinfo(title, message, parent=root)
        else:
            messagebox.showwarning(title, message, parent=root)
    finally:
        root.destroy()


def show_error(title: str, message: str, error_key: str = "", once_per_session: bool = True):
    """
    弹出错误对话框 + 写入日志。

    error_key: 错误标识，同一 key 本会话只弹一次（避免刷屏）
    once_per_session: False 则每次都弹
    """
    logging.error("%s: %s", title, message)

    if once_per_session and error_key:
        if error_key in _shown_errors:
            return
        _shown_errors.add(error_key)

    threading.Thread(
        target=lambda: _show_messagebox(title, message, "error"),
        daemon=True,
    ).start()


def show_warning(title: str, message: str, error_key: str = "", once_per_session: bool = True):
    """弹出警告对话框 + 写入日志。"""
    logging.warning("%s: %s", title, message)

    if once_per_session and error_key:
        if error_key in _shown_errors:
            return
        _shown_errors.add(error_key)

    threading.Thread(
        target=lambda: _show_messagebox(title, message, "warning"),
        daemon=True,
    ).start()


def clear_error_history():
    """清除会话错误记录（用于测试）。"""
    _shown_errors.clear()


# ── 托盘气泡通知 ──────────────────────────────────────────

# 聚合通知：短时间内多个归档合并为一条
_batch_lock = threading.Lock()
_batch_items: list[str] = []
_batch_timer: threading.Timer | None = None
_tray_icon = None  # 由 tray_app 注入

BATCH_INTERVAL = 2.0   # 聚合窗口（秒）
MAX_BATCH_ITEMS = 5     # 超过此数显示"等 N 个文件"


def set_tray_icon(icon):
    """注入托盘图标引用（由 tray_app 在创建图标后调用）。"""
    global _tray_icon
    _tray_icon = icon


def show_archive_notification(original_name: str, new_name: str, category: str):
    """
    显示归档完成通知。多个文件在 2 秒内聚合为一条。

    由 organizer.py 在归档成功后调用。
    """
    global _batch_timer

    item_text = f"{original_name} → {new_name}"

    with _batch_lock:
        _batch_items.append(item_text)

        # 取消之前的定时器
        if _batch_timer:
            _batch_timer.cancel()

        # 设置新的定时器
        _batch_timer = threading.Timer(BATCH_INTERVAL, _flush_batch)
        _batch_timer.daemon = True
        _batch_timer.start()


def _flush_batch():
    """将聚合的通知发送到托盘气泡。"""
    global _batch_timer

    with _batch_lock:
        items = list(_batch_items)
        _batch_items.clear()
        _batch_timer = None

    if not items or _tray_icon is None:
        return

    if len(items) == 1:
        title = "文件归档完成"
        message = items[0]
    elif len(items) <= MAX_BATCH_ITEMS:
        title = f"已归档 {len(items)} 个文件"
        message = "\n".join(items)
    else:
        title = f"已归档 {len(items)} 个文件"
        message = "\n".join(items[:MAX_BATCH_ITEMS]) + f"\n...等共 {len(items)} 个文件"

    try:
        _tray_icon.notify(message, title)
    except Exception:
        # 通知失败不影响归档（某些系统可能不支持气泡）
        pass


# ── 首次使用引导窗口 ──────────────────────────────────────

def show_welcome_window(configure_callback=None):
    """
    首次使用引导窗口。
    在 config 不存在或 AI Key 为空时显示。
    """
    root = tk.Tk()
    root.title("欢迎使用文件归档助手")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)

    # 标题
    ttk.Label(
        frame,
        text="📁 欢迎使用文件归档助手！",
        font=("Microsoft YaHei UI", 12, "bold"),
    ).pack(anchor="w", pady=(0, 16))

    # 说明
    intro_text = (
        "我会帮你自动整理文件：\n\n"
        "① 配置 AI 智能识别（推荐）\n"
        "   免费注册 DeepSeek 获取 API Key\n"
        "   程序会自动识别文档类型并规范命名\n\n"
        "② 把文件放入 input 文件夹\n"
        "   或右键托盘图标 → 一键整理桌面\n\n"
        "③ 在 output 文件夹查看归档结果\n"
        "   文件按类型自动分类存放"
    )
    ttk.Label(frame, text=intro_text, wraplength=400).pack(anchor="w", pady=(0, 16))

    # 提示
    ttk.Label(
        frame,
        text="💡 不配置 AI 也可以使用基础命名模式",
        foreground="#666666",
    ).pack(anchor="w", pady=(0, 16))

    # 按钮
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(anchor="e")

    def on_skip():
        root.destroy()

    def on_configure():
        root.destroy()
        if configure_callback:
            threading.Thread(target=configure_callback, daemon=True).start()

    ttk.Button(btn_frame, text="配置 AI", command=on_configure).pack(
        side="right", padx=(8, 0)
    )
    ttk.Button(btn_frame, text="跳过", command=on_skip).pack(side="right")

    # 居中
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"+{x}+{y}")

    root.mainloop()


def should_show_welcome() -> bool:
    """
    判断是否需要显示首次使用引导。
    条件：settings.json 不存在 或 AI Key 为空。
    """
    import config
    config.reload_settings()

    settings_path = config.get_settings_path()
    if not settings_path.exists():
        return True

    if not config.has_api_key():
        return True

    return False
