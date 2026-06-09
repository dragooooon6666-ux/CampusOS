"""
归档引擎：AI 分析 → 路径生成 → 复制文件 → 写入数据库
"""

import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path

from backend.database import get_db
from backend.services.file_analyzer import analyze_file
from backend.utils.naming import NON_TEXT_EXTENSIONS as _NON_TEXT

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"
WINDOWS_INVALID = r'<>:"/\|?*'

# 文档类型 → 大类分组
DOC_TYPE_GROUP = {
    "策划案":"活动全流程","方案":"活动全流程","议程":"活动全流程",
    "新闻稿":"活动全流程","活动总结":"活动全流程","会议纪要":"活动全流程",
    "通知":"办公文书","申请书":"办公文书","证明":"办公文书",
    "发言稿":"办公文书","述职报告":"办公文书","报告":"办公文书",
    "简历":"个人信息","作业":"个人信息","论文":"个人信息","笔记":"个人信息",
    "统计表":"数据与表单","签到表":"数据与表单","预算表":"数据与表单",
    "物资清单":"数据与表单","通讯录":"数据与表单","排班表":"数据与表单","收集表":"数据与表单",
    "图片":"媒体文件","视频":"媒体文件",
    "其他文档":"其他分类","其他表格":"其他分类",
    "Word文档":"其他分类","Excel表格":"其他分类","PDF文档":"其他分类",
    "PPT演示":"其他分类","纯文本":"其他分类","压缩包":"其他分类","其他文件":"其他分类",
}


def _sanitize(name: str, max_len: int = 30) -> str:
    for c in WINDOWS_INVALID:
        name = name.replace(c, "")
    return name[:max_len].strip()


def _compute_md5(file_path: Path) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _get_org_folder_map() -> dict[int, str]:
    """组织 ID → 组织名 映射"""
    db = get_db()
    rows = db.execute("SELECT id, name FROM organizations").fetchall()
    db.close()
    return {r["id"]: r["name"] for r in rows}


def _build_dest_path(file_path: Path, org_id: int | None, folder_id: int | None,
                     doc_type: str, title: str, doc_date: str) -> Path:
    """构建目标路径：output/{组织}/{子分类}/{日期}-{类型}-{标题}.{扩展名}"""
    org_map = _get_org_folder_map()
    org_name = org_map.get(org_id, "未分类") if org_id else "未分类"

    folder_name = ""
    if folder_id:
        db = get_db()
        row = db.execute("SELECT name FROM folders WHERE id = ?", (folder_id,)).fetchone()
        db.close()
        if row:
            folder_name = row["name"]

    title_safe = _sanitize(title) if title else _sanitize(file_path.stem, 20)
    date_part = doc_date if doc_date else datetime.now().strftime("%Y年%m月%d日")
    filename = f"{date_part}-{doc_type}-{title_safe}{file_path.suffix.lower()}"

    # 用大类分组作子文件夹
    group = DOC_TYPE_GROUP.get(doc_type, "其他分类")
    if folder_name:
        dest_dir = OUTPUT_DIR / org_name / folder_name
    else:
        dest_dir = OUTPUT_DIR / org_name / group

    return dest_dir / filename


def archive_file(file_path: Path, org_id: int | None = None, folder_id: int | None = None) -> dict | None:
    """
    归档一个文件：分析 → 生成路径 → 复制 → 写入数据库。
    返回数据库 file 记录，失败返回 None。
    """
    if not file_path.exists():
        return None

    # 0. 去重：相同内容哈希的文件不重复归档
    content_hash = _compute_md5(file_path)
    db = get_db()
    existing = db.execute(
        "SELECT id FROM files WHERE content_hash = ? LIMIT 1", (content_hash,)
    ).fetchone()
    if existing:
        db.close()
        return None

    # 1. AI 分析
    ext = file_path.suffix.lower()
    analysis = None
    if ext not in _NON_TEXT:
        analysis = analyze_file(file_path)

    if analysis:
        doc_type = analysis["doc_type"]
        title = analysis["title"]
        doc_date = analysis["doc_date"]
        author = analysis["author"]
    else:
        # 非文本文件：按扩展名回退
        from backend.utils.naming import get_file_category_label
        doc_type = get_file_category_label(file_path)
        title = file_path.stem
        doc_date = ""
        author = ""

    # 2. 构建目标路径
    dest_path = _build_dest_path(file_path, org_id, folder_id, doc_type, title, doc_date)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. 防重名
    counter = 1
    original = dest_path
    while dest_path.exists():
        stem = original.stem
        dest_path = original.parent / f"{stem}({counter}){original.suffix}"
        counter += 1

    # 4. 复制
    shutil.copy2(file_path, dest_path)

    # 5. 写入数据库
    db = get_db()
    cur = db.execute(
        """INSERT INTO files (original_name, stored_name, original_path, stored_path,
           extension, size_bytes, doc_type, title, doc_date, author, content_hash,
           folder_id, organization_id, ai_analyzed)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            file_path.name,
            dest_path.name,
            str(file_path),
            str(dest_path),
            file_path.suffix.lower(),
            file_path.stat().st_size,
            doc_type,
            title,
            doc_date,
            author,
            content_hash,
            folder_id,
            org_id,
            1 if analysis else 0,
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM files WHERE id = ?", (cur.lastrowid,)).fetchone()
    db.close()

    logger.info("归档: %s → %s", file_path.name, dest_path.relative_to(OUTPUT_DIR))
    return dict(row)
