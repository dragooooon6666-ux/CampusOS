"""
项目服务 — CRUD + AI 文件匹配
"""

import re
from difflib import SequenceMatcher

from backend.database import get_db


def similarity(a: str, b: str) -> float:
    """计算两个字符串的相似度（0-1）"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def match_file_to_project(file_id: int) -> list[int]:
    """
    分析文件内容关键词，返回匹配的项目 ID 列表（相似度 > 60%）。
    """
    db = get_db()
    file_row = db.execute(
        "SELECT title, doc_type, author FROM files WHERE id = ?", (file_id,)
    ).fetchone()
    if not file_row:
        db.close()
        return []

    # 构建文件搜索关键词
    keywords = " ".join(filter(None, [
        file_row["title"] or "",
        file_row["doc_type"] or "",
        file_row["author"] or "",
    ]))

    projects = db.execute("SELECT id, name, description FROM projects").fetchall()
    db.close()

    matches = []
    for p in projects:
        proj_text = f"{p['name']} {p['description'] or ''}"
        sim = similarity(keywords, proj_text)
        if sim > 0.6:
            matches.append((p["id"], sim))

    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches]


def auto_link_file(file_id: int) -> list[int]:
    """
    自动匹配并关联文件到项目。
    相似度 > 70%：自动关联
    返回关联成功的项目 ID 列表。
    """
    matches = match_file_to_project(file_id)

    db = get_db()
    # 获取实际相似度
    file_row = db.execute(
        "SELECT title, doc_type, author FROM files WHERE id = ?", (file_id,)
    ).fetchone()
    keywords = " ".join(filter(None, [
        file_row["title"] or "", file_row["doc_type"] or "", file_row["author"] or ""
    ]))

    linked = []
    for pid in matches:
        proj = db.execute("SELECT name, description FROM projects WHERE id = ?", (pid,)).fetchone()
        proj_text = f"{proj['name']} {proj['description'] or ''}"
        sim = similarity(keywords, proj_text)
        if sim > 0.7:  # >70% 自动关联
            try:
                db.execute(
                    "INSERT OR IGNORE INTO project_files (project_id, file_id, match_method) VALUES (?, ?, 'ai')",
                    (pid, file_id),
                )
                linked.append(pid)
            except Exception:
                pass

    db.commit()
    db.close()
    return linked


def list_projects(status: str | None = None, org_id: int | None = None):
    db = get_db()
    sql = "SELECT p.*, COUNT(pf.file_id) as file_count FROM projects p LEFT JOIN project_files pf ON p.id = pf.project_id WHERE 1=1"
    params = []
    if status:
        sql += " AND p.status = ?"
        params.append(status)
    if org_id:
        sql += " AND p.organization_id = ?"
        params.append(org_id)
    sql += " GROUP BY p.id ORDER BY p.updated_at DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_project(project_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        db.close()
        return None

    files = db.execute(
        """SELECT f.* FROM files f
           JOIN project_files pf ON f.id = pf.file_id
           WHERE pf.project_id = ? ORDER BY f.created_at DESC""",
        (project_id,),
    ).fetchall()
    docs = db.execute(
        "SELECT * FROM documents WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    ).fetchall()
    db.close()

    result = dict(row)
    result["files"] = [dict(f) for f in files]
    result["documents"] = [dict(d) for d in docs]
    return result


def create_project(data: dict):
    db = get_db()
    cur = db.execute(
        """INSERT INTO projects (name, description, status, leader, icon, start_date, end_date, organization_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("name", ""),
            data.get("description", ""),
            data.get("status", "active"),
            data.get("leader", ""),
            data.get("icon", "📋"),
            data.get("start_date", ""),
            data.get("end_date", ""),
            data.get("organization_id"),
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
    db.close()
    return dict(row)


def update_project(project_id: int, data: dict):
    db = get_db()
    allowed = ["name", "description", "status", "leader", "icon", "start_date", "end_date", "organization_id"]
    updates = {k: data[k] for k in allowed if k in data}
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE projects SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (*updates.values(), project_id))
        db.commit()
    row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    db.close()
    return dict(row)


def delete_project(project_id: int):
    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    db.close()


def link_file(project_id: int, file_id: int):
    db = get_db()
    try:
        db.execute(
            "INSERT OR IGNORE INTO project_files (project_id, file_id, match_method) VALUES (?, ?, 'manual')",
            (project_id, file_id),
        )
        db.commit()
    finally:
        db.close()


def unlink_file(project_id: int, file_id: int):
    db = get_db()
    db.execute("DELETE FROM project_files WHERE project_id = ? AND file_id = ?", (project_id, file_id))
    db.commit()
    db.close()


def generate_archive(project_id: int) -> str:
    """生成项目档案 Markdown"""
    project = get_project(project_id)
    if not project:
        return ""

    lines = [
        f"# {project['name']}",
        "",
        f"- **负责人**：{project['leader'] or '—'}",
        f"- **状态**：{project['status']}",
        f"- **时间**：{project['start_date'] or '—'} 至 {project['end_date'] or '—'}",
        "",
        "## 关联文件",
    ]
    for f in project.get("files", []):
        lines.append(f"- {f['doc_date']} | {f['doc_type']} | {f['title'] or f['original_name']}")

    lines.append("\n## 生成文档")
    for d in project.get("documents", []):
        lines.append(f"- {d['doc_type']} | {d['title']}")

    return "\n".join(lines)
