"""
托盘菜单用的配置窗口（tkinter）
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

import config
from dedupe import remove_duplicates_in_output

_dialog_lock = threading.Lock()

_PROVIDER_OPTIONS = [
    ("openai", "OpenAI"),
    ("deepseek", "DeepSeek"),
    ("kimi", "Kimi"),
]


def _mask_key(api_key: str) -> str:
    if not api_key:
        return "（未配置）"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"


def _safe_update_menu(icon):
    if icon is None:
        return
    try:
        icon.update_menu()
    except Exception:
        pass


def _show_message(title: str, message: str, msg_type: str = "warning"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        if msg_type == "info":
            messagebox.showinfo(title, message, parent=root)
        elif msg_type == "yesno":
            return messagebox.askyesno(title, message, parent=root)
        else:
            messagebox.showwarning(title, message, parent=root)
    finally:
        root.destroy()


def _run_in_dialog_thread(target):
    if not _dialog_lock.acquire(blocking=False):
        _show_message("提示", "已有配置窗口处于打开状态，请先关闭后再试。", "warning")
        return

    def runner():
        try:
            target()
        finally:
            _dialog_lock.release()

    threading.Thread(target=runner, daemon=True).start()


def _provider_label_to_id(label: str) -> str:
    for provider_id, provider_label in _PROVIDER_OPTIONS:
        if provider_label == label:
            return provider_id
    return "openai"


def _open_api_key_window(icon=None):
    root = tk.Tk()
    root.title("配置 AI")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    current_provider = config.get_ai_provider()

    ttk.Label(
        frame,
        text="AI 模型配置",
        font=("Microsoft YaHei UI", 10, "bold"),
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

    ttk.Label(frame, text="模型平台：").grid(row=1, column=0, sticky="w", pady=4)
    provider_var = tk.StringVar(value=config.get_provider_label(current_provider))
    provider_box = ttk.Combobox(
        frame,
        textvariable=provider_var,
        values=[label for _, label in _PROVIDER_OPTIONS],
        state="readonly",
        width=38,
    )
    provider_box.grid(row=1, column=1, sticky="w", pady=4)

    ttk.Label(frame, text="API Key：").grid(row=2, column=0, sticky="w", pady=(12, 4))
    key_entry = ttk.Entry(frame, width=42, show="*")
    key_entry.grid(row=2, column=1, sticky="w", pady=(12, 4))

    ttk.Label(frame, text="模型名称：").grid(row=3, column=0, sticky="w", pady=4)
    model_entry = ttk.Entry(frame, width=42)
    model_entry.grid(row=3, column=1, sticky="w", pady=4)

    hint_label = ttk.Label(frame, text="", foreground="#666666", wraplength=360)
    hint_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 12))

    status_label = ttk.Label(frame, text="")
    status_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 12))

    button_row = ttk.Frame(frame)
    button_row.grid(row=6, column=0, columnspan=2, sticky="e")

    def refresh_form(*_args):
        provider_id = _provider_label_to_id(provider_var.get())
        info = config.get_provider_info(provider_id)

        saved_key = config.get_ai_api_key(provider_id)
        if config.get_api_key_source(provider_id) == "环境变量":
            key_entry.delete(0, tk.END)
            key_entry.insert(0, saved_key)
            key_entry.config(state="readonly")
        else:
            key_entry.config(state="normal")
            key_entry.delete(0, tk.END)
            key_entry.insert(0, saved_key)

        model_entry.delete(0, tk.END)
        custom_model = config.AI_MODEL if provider_id == config.get_ai_provider() else ""
        model_entry.insert(0, custom_model or info["model"])

        hint_label.config(
            text=(
                f"获取 Key：{info['key_url']}\n"
                f"默认模型：{info['model']}（可留空使用默认）\n"
                "各平台 Key 分开保存，切换平台不会丢失已填写的 Key。"
            )
        )
        status_label.config(
            text=f"当前平台 Key 状态：{config.get_api_key_source(provider_id)}  {_mask_key(saved_key)}"
        )

    def close_window():
        root.quit()
        root.destroy()

    def on_save():
        provider_id = _provider_label_to_id(provider_var.get())
        api_key = key_entry.get().strip()
        model = model_entry.get().strip()

        if not api_key:
            messagebox.showwarning("提示", "API Key 不能为空。", parent=root)
            return

        default_model = config.get_provider_info(provider_id)["model"]
        if model == default_model:
            model = ""

        config.save_ai_config(provider_id, api_key, model)
        messagebox.showinfo("成功", f"{config.get_provider_label(provider_id)} 配置已保存。", parent=root)
        _safe_update_menu(icon)
        close_window()

    def on_clear():
        provider_id = _provider_label_to_id(provider_var.get())
        if messagebox.askyesno(
            "确认",
            f"确定清除 {config.get_provider_label(provider_id)} 的 API Key 吗？",
            parent=root,
        ):
            config.clear_ai_api_key(provider_id)
            messagebox.showinfo("完成", "已清除 API Key。", parent=root)
            _safe_update_menu(icon)
            close_window()

    def on_cancel():
        close_window()

    provider_box.bind("<<ComboboxSelected>>", refresh_form)
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    ttk.Button(button_row, text="保存", command=on_save).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(button_row, text="清除", command=on_clear).grid(row=0, column=1, padx=(0, 8))
    ttk.Button(button_row, text="取消", command=on_cancel).grid(row=0, column=2)

    refresh_form()
    key_entry.focus_set()
    root.update_idletasks()
    root.mainloop()


def configure_api_key(icon=None, item=None):
    _run_in_dialog_thread(lambda: _open_api_key_window(icon))


def toggle_ai_mode_with_check(icon, item):
    new_value = config.toggle_ai_mode()
    _safe_update_menu(icon)

    if new_value and not config.has_api_key():

        def show_warning():
            _show_message(
                "需要 API Key",
                "已开启 AI 命名，但尚未配置 API Key。\n\n"
                "请在托盘菜单选择「配置 AI」填写。\n"
                "未配置时将自动使用 V1 规则命名。",
            )

        threading.Thread(target=show_warning, daemon=True).start()


def _dedupe_output_worker():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    confirmed = messagebox.askyesno(
        "一键清理重复文件",
        "将扫描 output 各分类文件夹，按文件内容比对。\n\n"
        "内容完全相同的重复文件会被删除，\n"
        "每组只保留「最近修改」的那一份。\n\n"
        "input 文件夹不受影响。确定继续？",
        parent=root,
    )

    if not confirmed:
        root.destroy()
        return

    result = remove_duplicates_in_output()

    if result["deleted_count"] == 0:
        message = "未发现重复文件，无需清理。"
    else:
        message = (
            f"清理完成！\n\n"
            f"删除重复文件：{result['deleted_count']} 个\n"
            f"保留最新副本：{result['kept_count']} 个\n"
            f"重复组数：{result['duplicate_groups']} 组"
        )

    messagebox.showinfo("一键清理重复文件", message, parent=root)
    root.destroy()


def dedupe_output_files(icon=None, item=None):
    _run_in_dialog_thread(_dedupe_output_worker)
