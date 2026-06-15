"""CampusOS 启动器 — PyInstaller 入口"""
import sys
import os

if getattr(sys, 'frozen', False):
    # 工作目录 = exe 所在目录（用户放文件的地方）
    base = os.path.dirname(sys.executable)
    os.chdir(base)
    for d in ['input', 'output', 'data', 'config', 'templates']:
        os.makedirs(os.path.join(base, d), exist_ok=True)
    # 把 _MEIPASS 加入 sys.path，Python 才能 import backend
    sys.path.insert(0, sys._MEIPASS)
    # 首次运行：从模板创建 settings.json（不含 API Key）
    import shutil
    settings_dest = os.path.join(base, 'config', 'settings.json')
    if not os.path.exists(settings_dest):
        settings_src = os.path.join(sys._MEIPASS, 'config', 'settings.example.json')
        if os.path.exists(settings_src):
            shutil.copy(settings_src, settings_dest)
    # 修复: PyInstaller console=False 导致 stdout/stderr 为 None，
    # uvicorn 日志初始化调用 .isatty() 时崩溃
    if sys.stdout is None or sys.stderr is None:
        log_path = os.path.join(base, 'data', 'campusos.log')
        f = open(log_path, 'a')
        if sys.stdout is None:
            sys.stdout = f
        if sys.stderr is None:
            sys.stderr = f

import uvicorn
import webbrowser
import threading
import time
import urllib.request

def _campusos_already_running():
    """检测是否已有 CampusOS 在 8000 端口运行"""
    try:
        req = urllib.request.Request("http://localhost:8000/api/health")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

if _campusos_already_running():
    # 已有实例在运行，直接打开浏览器
    webbrowser.open("http://localhost:8000")
else:
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    try:
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="info")
    except Exception:
        # 端口可能被抢占 — 再次检查是否已有实例响应
        if _campusos_already_running():
            webbrowser.open("http://localhost:8000")
        else:
            print("启动失败，请查看 data/campusos.log", file=sys.stderr)
            raise
