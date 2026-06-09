"""
多源文件监控 — 基于 watchdog，支持热添加/移除监控源
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

STABLE_WAIT = 3.0          # 文件稳定等待秒数
POLL_INTERVAL = 1.0        # 事件检查间隔


class _NewFileHandler(FileSystemEventHandler):
    """watchdog 事件处理器：捕获新创建/修改完成的文件"""

    def __init__(self, source_id: int, callback: Callable):
        self.source_id = source_id
        self.callback = callback
        self._pending: dict[str, float] = {}  # path → first_seen_time

    def on_created(self, event):
        if not event.is_directory:
            self._note(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._note(event.src_path)

    def _note(self, path: str):
        now = time.time()
        if path not in self._pending:
            self._pending[path] = now

    def check_stable(self):
        """检查待处理文件是否稳定（大小不再变化），稳定则回调。"""
        now = time.time()
        ready = []
        for path, first_seen in list(self._pending.items()):
            p = Path(path)
            if not p.exists():
                del self._pending[path]
                continue
            if now - first_seen < STABLE_WAIT:
                continue
            try:
                size_before = p.stat().st_size
                time.sleep(0.5)
                if not p.exists():
                    del self._pending[path]
                    continue
                size_after = p.stat().st_size
                if size_before == size_after and size_before > 0:
                    ready.append(p)
                    del self._pending[path]
            except OSError:
                pass
        for p in ready:
            try:
                self.callback(p, self.source_id)
            except Exception:
                logger.exception("文件回调异常: %s", p)


class MonitorManager:
    """管理多个 watchdog 监控源"""

    def __init__(self, on_new_file: Callable[[Path, int], None] | None = None):
        self._observer = Observer()
        self._handlers: dict[int, _NewFileHandler] = {}
        self._on_new_file = on_new_file
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def add_source(self, source_id: int, path: str) -> bool:
        """添加监控源。返回 True 表示成功。"""
        p = Path(path)
        if not p.exists():
            logger.warning("监控源路径不存在: %s", path)
            return False
        with self._lock:
            if source_id in self._handlers:
                return True
            handler = _NewFileHandler(source_id, self._on_new_file or self._default_callback)
            self._observer.schedule(handler, str(p), recursive=False)
            self._handlers[source_id] = handler
            logger.info("已添加监控源 [%s]: %s", source_id, path)
            return True

    def remove_source(self, source_id: int):
        with self._lock:
            if source_id not in self._handlers:
                return
            handler = self._handlers.pop(source_id)
            self._observer.unschedule(handler)

    def start(self):
        self._observer.start()
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("文件监控已启动")

    def stop(self):
        self._running = False
        self._observer.stop()
        self._observer.join(timeout=5)
        logger.info("文件监控已停止")

    def _poll_loop(self):
        while self._running:
            with self._lock:
                handlers = list(self._handlers.values())
            for h in handlers:
                try:
                    h.check_stable()
                except Exception:
                    pass
            time.sleep(POLL_INTERVAL)

    def _default_callback(self, file_path: Path, source_id: int):
        logger.info("新文件检测 [source=%s]: %s", source_id, file_path.name)


# 全局实例
monitor = MonitorManager()
