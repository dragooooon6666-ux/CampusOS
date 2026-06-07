"""
文件自动归档 - 核心逻辑（与 UI 无关）

output 文件夹按内容类型分类：
- AI 模式：简历/作业/论文/策划案/方案/议程/会议纪要/活动总结/报告/申请书/通知/证明/笔记/其他文档
- V1 回退：Word/Excel/PDF/图片/视频/压缩包/其他
"""

import logging
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from naming import (
    generate_new_filename,
    get_unique_dest_path,
    get_file_extension_category,
)
from notify import show_error, show_warning


def _get_base_dir() -> Path:
    """开发时用项目目录；打包成 exe 后用 exe 所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _get_base_dir()

INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# ── 输出分类 ──────────────────────────────────────────────

# AI 模式：按文档内容分类（大学生场景）
CONTENT_CATEGORIES = [
    "简历",
    "作业",
    "论文",
    "策划案",
    "方案",
    "议程",
    "会议纪要",
    "活动总结",
    "报告",
    "申请书",
    "通知",
    "证明",
    "笔记",
    "其他文档",
]

# V1 回退：按文件扩展名分类
FILE_TYPE_CATEGORIES = [
    "Word",
    "Excel",
    "PDF",
    "图片",
    "视频",
    "压缩包",
    "其他",
]

# 所有可能的分类（需要创建文件夹）
ALL_CATEGORIES = CONTENT_CATEGORIES + FILE_TYPE_CATEGORIES


# ── 目录初始化 ────────────────────────────────────────────

def setup_directories():
    """创建所有必需的目录（含所有分类子文件夹）。"""
    for folder in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR, CONFIG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    for category in ALL_CATEGORIES:
        (OUTPUT_DIR / category).mkdir(parents=True, exist_ok=True)


# ── 日志 ──────────────────────────────────────────────────

def setup_logging():
    log_file = get_today_log_file()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
        datefmt="%H:%M:%S",
        filename=log_file,
        encoding="utf-8",
        force=True,
    )


def get_today_log_file() -> Path:
    return LOGS_DIR / f"{datetime.now():%Y-%m-%d}.log"


# ── 核心归档 ──────────────────────────────────────────────

def get_file_category(file_path: Path) -> str:
    """根据扩展名获取分类（仅用于 V1 回退或非文本文档）。"""
    return get_file_extension_category(file_path)


def get_dest_path(file_path: Path) -> tuple[Path, str]:
    """
    生成目标路径。返回 (dest_path, category)。

    命名由 generate_new_filename 统一处理：
    - AI 模式：category 为内容类型，文件存入对应子文件夹
    - V1 回退：category 为扩展名类型
    """
    filename, category = generate_new_filename(file_path)
    dest_dir = OUTPUT_DIR / category
    dest_path = get_unique_dest_path(dest_dir, filename)
    return (dest_path, category)


def archive_file(file_path: Path) -> Path:
    """归档单个文件：生成目标路径 → 复制 → 返回目标路径。"""
    try:
        dest_path, _category = get_dest_path(file_path)
        shutil.copy2(file_path, dest_path)
        return dest_path
    except PermissionError:
        show_error(
            "权限不足",
            f"无法读取或写入文件：\n{file_path.name}\n\n请检查文件是否被其他程序占用。",
            error_key="permission_error",
        )
        raise
    except OSError as e:
        show_error(
            "文件操作失败",
            f"归档文件时出错：\n{file_path.name}\n\n{str(e)}",
            error_key=f"os_error_{type(e).__name__}",
        )
        raise


def _wait_file_stable(file_path: Path, max_wait: float = 10.0, check_interval: float = 0.5) -> bool:
    """等待文件大小稳定（写入完成），返回 True 表示稳定，超时返回 False。"""
    waited = 0.0
    while waited < max_wait:
        if not file_path.exists():
            return False
        size_before = file_path.stat().st_size
        time.sleep(check_interval)
        waited += check_interval
        if not file_path.exists():
            return False
        size_after = file_path.stat().st_size
        if size_before == size_after and size_before > 0:
            return True
    return True


def get_file_key(file_path: Path) -> tuple:
    stat = file_path.stat()
    return (file_path.name, stat.st_mtime_ns, stat.st_size)


def archive_and_report(file_path: Path) -> Path:
    """
    归档并记录，成功后调用通知回调（如果已设置）。

    _archive_callback 由 OrganizerService.set_archive_callback() 注入。
    """
    try:
        dest_path, category = get_dest_path(file_path)
        shutil.copy2(file_path, dest_path)
        logging.info("归档: %s -> %s/%s", file_path.name, category, dest_path.name)

        # 发送托盘通知
        if _archive_callback:
            try:
                _archive_callback(file_path.name, dest_path.name, category)
            except Exception:
                pass  # 通知失败不影响归档

        return dest_path
    except Exception:
        logging.exception("归档失败: %s", file_path.name)
        raise


# 归档通知回调（由 tray_app 通过 OrganizerService.set_archive_callback 注入）
_archive_callback = None


# ── 监控服务 ──────────────────────────────────────────────

class OrganizerService:
    """后台监控服务，支持开启/暂停/停止。"""

    def __init__(self, poll_interval: float = 2.0):
        self.poll_interval = poll_interval
        self.processed_keys: set = set()
        self.monitoring_enabled = True
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def set_archive_callback(self, callback):
        """注入归档通知回调（由 tray_app 调用）。"""
        global _archive_callback
        _archive_callback = callback

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        try:
            setup_directories()
        except PermissionError:
            show_error(
                "权限不足",
                "无法创建 input/output 文件夹。\n\n请检查程序所在目录是否有写入权限。",
                error_key="startup_permission",
            )
            raise
        except OSError as e:
            show_error(
                "启动失败",
                f"无法初始化工作目录：\n{str(e)}",
                error_key="startup_dir_error",
            )
            raise

        setup_logging()
        logging.info("程序启动（托盘模式）")
        self.processed_keys = self._process_existing_files()

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def pause_monitoring(self):
        self.monitoring_enabled = False
        logging.info("监控已暂停")

    def resume_monitoring(self):
        self.monitoring_enabled = True
        logging.info("监控已恢复")

    def toggle_monitoring(self):
        if self.monitoring_enabled:
            self.pause_monitoring()
        else:
            self.resume_monitoring()

    def stop(self):
        self._stop_event.set()
        logging.info("程序结束")
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.poll_interval + 2)

    def _process_existing_files(self) -> set:
        files = [f for f in INPUT_DIR.iterdir() if f.is_file()]
        processed_keys = set()

        if not files:
            logging.info("input 文件夹为空，等待新文件...")
            return processed_keys

        logging.info("开始归档，共 %d 个文件", len(files))

        for file_path in sorted(files):
            archive_and_report(file_path)
            processed_keys.add(get_file_key(file_path))

        logging.info("本次归档完成")
        return processed_keys

    def _watch_loop(self):
        logging.info("开始监控 input 文件夹")

        while not self._stop_event.is_set():
            if self.monitoring_enabled:
                self._check_new_files()

            self._stop_event.wait(self.poll_interval)

    def _check_new_files(self):
        for file_path in INPUT_DIR.iterdir():
            if self._stop_event.is_set():
                return

            if not file_path.is_file():
                continue

            with self._lock:
                file_key = get_file_key(file_path)
                if file_key in self.processed_keys:
                    continue

            if not _wait_file_stable(file_path):
                continue

            if not file_path.exists():
                continue

            with self._lock:
                file_key = get_file_key(file_path)
                if file_key in self.processed_keys:
                    continue

                archive_and_report(file_path)
                self.processed_keys.add(file_key)
                logging.info("新文件归档完成")
