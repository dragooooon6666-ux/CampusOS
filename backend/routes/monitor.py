"""监控源管理 — CRUD API"""

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models.monitor import MonitorSourceCreate, MonitorSourceUpdate, MonitorSourceResponse
from backend.services.file_watcher import monitor

router = APIRouter(prefix="/api/monitor-sources", tags=["monitor"])


@router.get("", response_model=list[MonitorSourceResponse])
def list_sources():
    db = get_db()
    rows = db.execute(
        "SELECT id, path, label, enabled, created_at FROM monitor_sources ORDER BY id"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.post("", response_model=MonitorSourceResponse, status_code=201)
def create_source(data: MonitorSourceCreate):
    db = get_db()
    existing = db.execute(
        "SELECT id FROM monitor_sources WHERE path = ?", (data.path,)
    ).fetchone()
    if existing:
        db.close()
        raise HTTPException(409, "监控源已存在")

    cur = db.execute(
        "INSERT INTO monitor_sources (path, label, enabled) VALUES (?, ?, ?)",
        (data.path, data.label, int(data.enabled)),
    )
    db.commit()
    row = db.execute(
        "SELECT id, path, label, enabled, created_at FROM monitor_sources WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    db.close()

    if data.enabled:
        monitor.add_source(row["id"], data.path)

    return dict(row)


@router.put("/{source_id}", response_model=MonitorSourceResponse)
def update_source(source_id: int, data: MonitorSourceUpdate):
    db = get_db()
    existing = db.execute("SELECT id, enabled FROM monitor_sources WHERE id = ?", (source_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(404, "监控源不存在")

    updates = {}
    if data.label is not None:
        updates["label"] = data.label
    if data.enabled is not None:
        updates["enabled"] = int(data.enabled)

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE monitor_sources SET {sets} WHERE id = ?", (*updates.values(), source_id))
        db.commit()

    row = db.execute(
        "SELECT id, path, label, enabled, created_at FROM monitor_sources WHERE id = ?",
        (source_id,),
    ).fetchone()
    db.close()

    # 启停监控
    if data.enabled is not None:
        if data.enabled:
            monitor.add_source(source_id, row["path"])
        else:
            monitor.remove_source(source_id)

    return dict(row)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int):
    db = get_db()
    existing = db.execute("SELECT id FROM monitor_sources WHERE id = ?", (source_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(404, "监控源不存在")
    monitor.remove_source(source_id)
    db.execute("DELETE FROM monitor_sources WHERE id = ?", (source_id,))
    db.commit()
    db.close()
