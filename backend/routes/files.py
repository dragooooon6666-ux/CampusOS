"""文件管理 API"""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, UploadFile, File

from backend.services.file_extractor import process_entry

from backend.database import get_db
from backend.services.archiver import archive_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("")
def list_files(
    org_id: int | None = Query(None),
    folder_id: int | None = Query(None),
    doc_type: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    db = get_db()
    sql = "SELECT * FROM files WHERE 1=1"
    params = []

    if org_id:
        sql += " AND organization_id = ?"
        params.append(org_id)
    if folder_id:
        sql += " AND folder_id = ?"
        params.append(folder_id)
    if doc_type:
        sql += " AND doc_type = ?"
        params.append(doc_type)
    if search:
        sql += " AND (original_name LIKE ? OR title LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{file_id}")
def get_file(file_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "文件不存在")
    return dict(row)


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """拖拽/选择上传文件到 input 文件夹，自动归档。支持压缩包自动解压。"""
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    input_dir = BASE_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    errors = []
    extracted_info = []

    for f in files:
        try:
            dest = input_dir / f.filename
            counter = 1
            while dest.exists():
                stem, ext = Path(f.filename).stem, Path(f.filename).suffix
                dest = input_dir / f"{stem}({counter}){ext}"
                counter += 1

            with dest.open("wb") as out:
                shutil.copyfileobj(f.file, out)

            # 如果是压缩包，自动解压
            if dest.suffix.lower() == ".zip":
                result = process_entry(dest, input_dir)
                extracted_info.append(result["message"])
                # 归档解压出的文件
                for extracted in result["files"]:
                    try:
                        arch_result = archive_file(extracted)
                        if arch_result:
                            from backend.services.project_service import auto_link_file
                            linked = auto_link_file(arch_result["id"])
                            saved.append({
                                "file": extracted.name,
                                "doc_type": arch_result["doc_type"],
                                "title": arch_result.get("title", ""),
                                "file_id": arch_result["id"],
                                "linked_projects": linked,
                            })
                    except Exception:
                        pass
            else:
                # 普通文件直接归档
                arch_result = archive_file(dest)
                if arch_result:
                    from backend.services.project_service import auto_link_file
                    linked = auto_link_file(arch_result["id"])
                    saved.append({
                        "file": f.filename,
                        "doc_type": arch_result["doc_type"],
                        "title": arch_result.get("title", ""),
                        "file_id": arch_result["id"],
                        "linked_projects": linked,
                    })
                else:
                    errors.append({"file": f.filename, "error": "归档失败（重复或无法识别）"})
        except Exception as e:
            errors.append({"file": f.filename, "error": str(e)})

    return {"saved": len(saved), "extracted": extracted_info, "files": saved}


@router.post("/scan", status_code=201)
def scan_input():
    """手动扫描 input 文件夹并归档所有文件"""
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    input_dir = BASE_DIR / "input"

    if not input_dir.exists():
        return {"scanned": 0, "archived": 0, "errors": []}

    files = [f for f in input_dir.iterdir() if f.is_file()]
    archived = 0
    errors = []

    for fp in files:
        try:
            result = archive_file(fp)
            if result:
                archived += 1
        except Exception as e:
            errors.append({"file": fp.name, "error": str(e)})

    return {"scanned": len(files), "archived": archived, "errors": errors}


@router.put("/{file_id}")
def update_file(file_id: int, data: dict):
    """更新文件属性（如手动改分类）"""
    db = get_db()
    row = db.execute("SELECT id FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "文件不存在")

    allowed = ["doc_type", "title", "folder_id", "organization_id"]
    updates = {k: data[k] for k in allowed if k in data}
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE files SET {sets} WHERE id = ?", (*updates.values(), file_id))
        db.commit()
    row = db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    db.close()
    return dict(row)


@router.get("/{file_id}/open")
def open_file_location(file_id: int):
    """在资源管理器中打开文件所在目录"""
    import os
    db = get_db()
    row = db.execute("SELECT stored_path FROM files WHERE id = ?", (file_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "文件不存在")
    path = Path(row["stored_path"])
    if path.exists():
        os.startfile(str(path.parent))
        return {"status": "ok"}
    # 文件不存在，尝试打开父目录
    if path.parent.exists():
        os.startfile(str(path.parent))
        return {"status": "ok", "warning": "文件已不存在，已打开所在目录"}
    raise HTTPException(404, "文件所在目录也不存在，可能已被删除")


@router.delete("/{file_id}", status_code=204)
def delete_file(file_id: int):
    db = get_db()
    row = db.execute("SELECT stored_path FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "文件不存在")

    # 删除物理文件
    try:
        Path(row["stored_path"]).unlink(missing_ok=True)
    except OSError:
        pass

    db.execute("DELETE FROM files WHERE id = ?", (file_id,))
    db.commit()
    db.close()
