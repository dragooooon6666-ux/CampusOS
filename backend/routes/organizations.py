"""组织管理 — CRUD API"""

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    FolderCreate,
    FolderUpdate,
    FolderResponse,
)

router = APIRouter(prefix="/api/orgs", tags=["organizations"])


# ── Organizations ──

@router.get("", response_model=list[OrganizationResponse])
def list_orgs():
    db = get_db()
    rows = db.execute(
        "SELECT id, name, icon, sort_order, created_at FROM organizations ORDER BY sort_order"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_org(org_id: int):
    db = get_db()
    row = db.execute(
        "SELECT id, name, icon, sort_order, created_at FROM organizations WHERE id = ?",
        (org_id,),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "组织不存在")
    return dict(row)


@router.post("", response_model=OrganizationResponse, status_code=201)
def create_org(data: OrganizationCreate):
    db = get_db()
    cur = db.execute(
        "INSERT INTO organizations (name, icon, sort_order) VALUES (?, ?, ?)",
        (data.name, data.icon, data.sort_order),
    )
    db.commit()
    row = db.execute(
        "SELECT id, name, icon, sort_order, created_at FROM organizations WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    db.close()
    return dict(row)


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_org(org_id: int, data: OrganizationUpdate):
    db = get_db()
    existing = db.execute("SELECT id FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(404, "组织不存在")

    updates = data.model_dump(exclude_unset=True)
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(
            f"UPDATE organizations SET {sets} WHERE id = ?",
            (*updates.values(), org_id),
        )
        db.commit()

    row = db.execute(
        "SELECT id, name, icon, sort_order, created_at FROM organizations WHERE id = ?",
        (org_id,),
    ).fetchone()
    db.close()
    return dict(row)


@router.delete("/{org_id}", status_code=204)
def delete_org(org_id: int):
    db = get_db()
    existing = db.execute("SELECT id FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(404, "组织不存在")
    db.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
    db.commit()
    db.close()


# ── Folders (子分类) ──

@router.get("/{org_id}/folders", response_model=list[FolderResponse])
def list_folders(org_id: int):
    db = get_db()
    rows = db.execute(
        "SELECT id, organization_id, name, sort_order, created_at FROM folders "
        "WHERE organization_id = ? ORDER BY sort_order",
        (org_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.post("/{org_id}/folders", response_model=FolderResponse, status_code=201)
def create_folder(org_id: int, data: FolderCreate):
    db = get_db()
    org = db.execute("SELECT id FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not org:
        db.close()
        raise HTTPException(404, "组织不存在")
    cur = db.execute(
        "INSERT INTO folders (organization_id, name, sort_order) VALUES (?, ?, ?)",
        (org_id, data.name, data.sort_order),
    )
    db.commit()
    row = db.execute(
        "SELECT id, organization_id, name, sort_order, created_at FROM folders WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    db.close()
    return dict(row)


@router.put("/{org_id}/folders/{folder_id}", response_model=FolderResponse)
def update_folder(org_id: int, folder_id: int, data: FolderUpdate):
    db = get_db()
    row = db.execute(
        "SELECT id FROM folders WHERE id = ? AND organization_id = ?",
        (folder_id, org_id),
    ).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "子分类不存在")

    updates = data.model_dump(exclude_unset=True)
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(
            f"UPDATE folders SET {sets} WHERE id = ?",
            (*updates.values(), folder_id),
        )
        db.commit()

    row = db.execute(
        "SELECT id, organization_id, name, sort_order, created_at FROM folders WHERE id = ?",
        (folder_id,),
    ).fetchone()
    db.close()
    return dict(row)


@router.delete("/{org_id}/folders/{folder_id}", status_code=204)
def delete_folder(org_id: int, folder_id: int):
    db = get_db()
    row = db.execute(
        "SELECT id FROM folders WHERE id = ? AND organization_id = ?",
        (folder_id, org_id),
    ).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "子分类不存在")
    db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    db.commit()
    db.close()
