"""
文件自动归档 - Windows 系统托盘外壳
"""

import os
import threading

import pystray
from PIL import Image, ImageDraw

import config
from organizer import (
    INPUT_DIR,
    LOGS_DIR,
    OUTPUT_DIR,
    OrganizerService,
    get_today_log_file,
)
from settings_ui import configure_api_key, dedupe_output_files, toggle_ai_mode_with_check
from notify import (
    set_tray_icon,
    show_welcome_window,
    should_show_welcome,
    show_archive_notification,
)


def create_tray_icon_image() -> Image.Image:
    """生成简单的文件夹风格托盘图标。"""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rectangle([10, 24, 54, 52], fill="#FBBF24", outline="#B45309")
    draw.rectangle([10, 16, 30, 26], fill="#F59E0B", outline="#B45309")
    draw.rectangle([18, 34, 46, 44], fill="#FFFFFF", outline="#D97706")

    return image


def open_path(path):
    os.startfile(str(path))


def open_input_folder(icon, item):
    open_path(INPUT_DIR)


def open_output_folder(icon, item):
    open_path(OUTPUT_DIR)


def open_log_file(icon, item):
    log_file = get_today_log_file()
    if log_file.exists():
        open_path(log_file)
    else:
        open_path(LOGS_DIR)


def toggle_monitoring(icon, item):
    service.toggle_monitoring()
    icon.update_menu()


def get_monitoring_label(item):
    return "暂停监控" if service.monitoring_enabled else "开启监控"


def get_ai_mode_label(item):
    return "关闭 AI 智能命名" if config.is_ai_mode_enabled() else "开启 AI 智能命名"


def get_api_key_status_label(item):
    provider = config.get_provider_label()
    source = config.get_api_key_source()
    return f"AI：{provider} | Key {source}"


def quit_app(icon, item):
    service.stop()
    icon.stop()


# 全局 service 实例
service = OrganizerService()

# 归档通知回调
def _on_file_archived(original_name: str, new_name: str, category: str):
    """文件归档成功后调用，发送托盘气泡通知。"""
    show_archive_notification(original_name, new_name, category)


service.set_archive_callback(_on_file_archived)


def build_menu():
    return pystray.Menu(
        pystray.MenuItem(get_monitoring_label, toggle_monitoring),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(get_ai_mode_label, toggle_ai_mode_with_check),
        pystray.MenuItem("配置 AI", configure_api_key),
        pystray.MenuItem(get_api_key_status_label, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("打开 input 文件夹", open_input_folder),
        pystray.MenuItem("打开 output 文件夹", open_output_folder),
        pystray.MenuItem("一键清理重复文件", dedupe_output_files),
        pystray.MenuItem("查看日志文件", open_log_file),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出程序", quit_app),
    )


def run_tray_app():
    # 1. 启动监控服务
    service.start()

    # 2. 创建托盘图标
    icon = pystray.Icon(
        "FileOrganizer",
        create_tray_icon_image(),
        "文件自动归档助手",
        build_menu(),
    )

    # 3. 注入图标给通知系统（气泡通知需要）
    set_tray_icon(icon)

    # 4. 首次使用引导（在图标创建后显示，确保窗口能正常弹出）
    if should_show_welcome():
        show_welcome_window(configure_callback=lambda: configure_api_key(icon))

    # 5. 运行托盘
    icon.run()


if __name__ == "__main__":
    run_tray_app()
