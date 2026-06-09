"""
CampusOS — FastAPI 入口
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes.organizations import router as orgs_router
from backend.routes.monitor import router as monitor_router
from backend.routes.files import router as files_router
from backend.routes.writing import router as writing_router
from backend.routes.projects import router as projects_router
from backend.routes.export import router as export_router
from backend.routes.settings_api import router as settings_api_router
from backend.services.file_watcher import monitor

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="CampusOS", version="0.1.0")

# CORS（开发时允许 localhost 任意端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()

    # 自动打开浏览器
    import webbrowser, threading
    def _open():
        import time; time.sleep(1)
        webbrowser.open("http://localhost:8000")
    threading.Thread(target=_open, daemon=True).start()

    # 设置监控回调：新文件 → 自动归档
    from backend.services.archiver import archive_file
    def on_file(path, source_id):
        try:
            archive_file(path)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("归档失败: %s", path)

    monitor._on_new_file = on_file

    # 加载已启用的监控源
    from backend.database import get_db
    db = get_db()
    sources = db.execute(
        "SELECT id, path FROM monitor_sources WHERE enabled = 1"
    ).fetchall()
    for s in sources:
        monitor.add_source(s["id"], s["path"])
    db.close()
    monitor.start()


@app.on_event("shutdown")
def shutdown():
    monitor.stop()


# ── 路由注册 ──
app.include_router(orgs_router)
app.include_router(monitor_router)
app.include_router(files_router)
app.include_router(writing_router)
app.include_router(projects_router)
app.include_router(export_router)
app.include_router(settings_api_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# ── 静态文件（前端） ──

frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    for sub in ["css", "js", "assets"]:
        sub_dir = frontend_dir / sub
        if sub_dir.exists():
            app.mount(f"/{sub}", StaticFiles(directory=str(sub_dir)), name=sub)


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """非 API 路径返回 SPA 入口。"""
    if full_path.startswith("api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(index_path))
    return {"detail": "Frontend not found"}, 404
