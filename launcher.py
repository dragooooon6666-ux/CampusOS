"""CampusOS 启动器 — PyInstaller 入口"""
import uvicorn
import webbrowser
import threading
import time
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

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

threading.Thread(target=open_browser, daemon=True).start()
uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="info")
