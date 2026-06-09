"""项目管理 API"""

from fastapi import APIRouter, HTTPException, Query

from backend.services.project_service import (
    list_projects, get_project, create_project, update_project, delete_project,
    link_file, unlink_file, auto_link_file, generate_archive,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def _list(status: str | None = None, org_id: int | None = None):
    return list_projects(status, org_id)


@router.get("/{project_id}")
def _get(project_id: int):
    p = get_project(project_id)
    if not p:
        raise HTTPException(404, "项目不存在")
    return p


@router.post("", status_code=201)
def _create(data: dict):
    if not data.get("name"):
        raise HTTPException(400, "项目名称不能为空")
    return create_project(data)


@router.put("/{project_id}")
def _update(project_id: int, data: dict):
    return update_project(project_id, data)


@router.delete("/{project_id}", status_code=204)
def _delete(project_id: int):
    delete_project(project_id)


@router.post("/{project_id}/link-file")
def _link(project_id: int, data: dict):
    file_id = data.get("file_id")
    if not file_id:
        raise HTTPException(400, "缺少 file_id")
    link_file(project_id, file_id)
    return {"status": "ok"}


@router.delete("/{project_id}/link-file/{file_id}", status_code=204)
def _unlink(project_id: int, file_id: int):
    unlink_file(project_id, file_id)


@router.post("/auto-link/{file_id}")
def _auto_link(file_id: int):
    linked = auto_link_file(file_id)
    return {"linked": linked}


@router.get("/{project_id}/archive")
def _archive(project_id: int):
    md = generate_archive(project_id)
    if not md:
        raise HTTPException(404, "项目不存在")
    return {"markdown": md}
