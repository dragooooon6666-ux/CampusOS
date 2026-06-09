"""项目导出 API — zip 打包"""

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.services.project_service import get_project, generate_archive

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/project/{project_id}")
def export_project(project_id: int):
    import traceback
    try:
        project = get_project(project_id)
        if not project:
            raise HTTPException(404, "项目不存在")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            archive_md = generate_archive(project_id)
            zf.writestr(f"{project['name']}/项目档案.md", archive_md)

            for f in project.get("files", []):
                src = Path(f["stored_path"])
                if src.exists():
                    zf.write(str(src), f"{project['name']}/文件/{f['stored_name']}")

            for d in project.get("documents", []):
                doc_name = f"{d['doc_type']}-{d['title']}.md"
                zf.writestr(f"{project['name']}/生成文档/{doc_name}", d["content"] or "")

        buf.seek(0)
        from urllib.parse import quote
        safe_name = project["name"].replace("/", "_").replace("\\", "_")
        from fastapi.responses import Response
        return Response(
            content=buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_name)}.zip"},
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))
