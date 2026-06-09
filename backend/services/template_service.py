"""
模板服务 — 文档模板 CRUD + 导入
"""

import json
from pathlib import Path

from backend.database import get_db

# ── 文档类型 → 表单字段定义 ──

FORM_FIELDS: dict[str, list[dict]] = {
    "新闻稿": [
        {"key": "event_name", "label": "活动名称", "type": "text", "required": True},
        {"key": "event_time", "label": "时间", "type": "text", "required": True},
        {"key": "event_place", "label": "地点", "type": "text", "required": True},
        {"key": "participants", "label": "参与单位/人员", "type": "textarea", "required": True},
        {"key": "content", "label": "主要内容描述", "type": "textarea", "required": False},
        {"key": "highlights", "label": "亮点/成果", "type": "textarea", "required": False},
    ],
    "活动总结": [
        {"key": "event_name", "label": "活动名称", "type": "text", "required": True},
        {"key": "event_time", "label": "时间", "type": "text", "required": True},
        {"key": "event_place", "label": "地点", "type": "text", "required": True},
        {"key": "process", "label": "活动过程", "type": "textarea", "required": True},
        {"key": "outcome", "label": "成果/数据", "type": "textarea", "required": False},
        {"key": "issues", "label": "存在问题", "type": "textarea", "required": False},
    ],
    "会议纪要": [
        {"key": "meeting_name", "label": "会议名称", "type": "text", "required": True},
        {"key": "meeting_time", "label": "时间", "type": "text", "required": True},
        {"key": "meeting_place", "label": "地点", "type": "text", "required": True},
        {"key": "attendees", "label": "参会人员", "type": "textarea", "required": True},
        {"key": "agenda", "label": "会议议题", "type": "textarea", "required": True},
        {"key": "discussion", "label": "讨论要点", "type": "textarea", "required": False},
    ],
    "通知": [
        {"key": "title", "label": "通知标题", "type": "text", "required": True},
        {"key": "body", "label": "通知内容", "type": "textarea", "required": True},
        {"key": "deadline", "label": "截止时间", "type": "text", "required": False},
        {"key": "contact", "label": "联系方式", "type": "text", "required": False},
    ],
    "请示": [
        {"key": "title", "label": "请示事由", "type": "text", "required": True},
        {"key": "reason", "label": "背景/原因", "type": "textarea", "required": True},
        {"key": "request", "label": "具体请求事项", "type": "textarea", "required": True},
    ],
    "申请书": [
        {"key": "applicant", "label": "申请人", "type": "text", "required": True},
        {"key": "apply_for", "label": "申请事项", "type": "text", "required": True},
        {"key": "reason", "label": "申请理由", "type": "textarea", "required": True},
    ],
    "发言稿": [
        {"key": "occasion", "label": "发言场合", "type": "text", "required": True},
        {"key": "speaker", "label": "发言人", "type": "text", "required": True},
        {"key": "audience", "label": "听众", "type": "text", "required": False},
        {"key": "key_points", "label": "发言要点", "type": "textarea", "required": True},
    ],
    "工作汇报": [
        {"key": "period", "label": "汇报周期", "type": "text", "required": True},
        {"key": "completed", "label": "已完成工作", "type": "textarea", "required": True},
        {"key": "planned", "label": "下阶段计划", "type": "textarea", "required": False},
        {"key": "issues", "label": "存在问题", "type": "textarea", "required": False},
    ],
    "述职报告": [
        {"key": "name", "label": "述职人", "type": "text", "required": True},
        {"key": "position", "label": "职务", "type": "text", "required": True},
        {"key": "period", "label": "述职周期", "type": "text", "required": True},
        {"key": "achievements", "label": "主要成绩", "type": "textarea", "required": True},
        {"key": "reflection", "label": "不足与反思", "type": "textarea", "required": False},
    ],
    "评优材料": [
        {"key": "candidate", "label": "申报人/集体", "type": "text", "required": True},
        {"key": "award", "label": "申报奖项", "type": "text", "required": True},
        {"key": "deeds", "label": "主要事迹", "type": "textarea", "required": True},
        {"key": "evidence", "label": "支撑材料说明", "type": "textarea", "required": False},
    ],
    "项目申报书": [
        {"key": "project_name", "label": "项目名称", "type": "text", "required": True},
        {"key": "team", "label": "团队信息", "type": "textarea", "required": True},
        {"key": "background", "label": "项目背景", "type": "textarea", "required": True},
        {"key": "plan", "label": "实施方案", "type": "textarea", "required": True},
        {"key": "budget", "label": "经费预算", "type": "textarea", "required": False},
    ],
}

# 通用兜底
_DEFAULT_FIELDS = [
    {"key": "title", "label": "文档标题", "type": "text", "required": True},
    {"key": "content", "label": "主要内容", "type": "textarea", "required": True},
]


def get_form_fields(doc_type: str) -> list[dict]:
    """根据文档类型返回表单字段定义"""
    return FORM_FIELDS.get(doc_type, _DEFAULT_FIELDS)


def list_templates(doc_type: str | None = None):
    db = get_db()
    if doc_type:
        rows = db.execute(
            "SELECT * FROM templates WHERE doc_type = ? ORDER BY is_builtin DESC, id",
            (doc_type,),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM templates ORDER BY is_builtin DESC, id").fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_template(template_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def create_template(name: str, doc_type: str, style: str, sections: list[dict], formatting: dict | None = None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO templates (name, doc_type, style, sections, formatting, is_builtin) VALUES (?, ?, ?, ?, ?, 0)",
        (name, doc_type, style, json.dumps(sections, ensure_ascii=False),
         json.dumps(formatting or {}, ensure_ascii=False)),
    )
    db.commit()
    row = db.execute("SELECT * FROM templates WHERE id = ?", (cur.lastrowid,)).fetchone()
    db.close()
    return dict(row)


def import_template_from_file(file_path: Path) -> dict | None:
    """从文档文件导入模板结构。分析文档 → 提取 sections。"""
    from backend.services.file_analyzer import _call_chat_api

    prompt = f"""分析以下文档的结构，提取其章节/段落划分，生成模板 sections。

每个 section 包含：
- key: 英文标识
- label: 中文标签
- ai_role: AI 生成该段落的角色描述（一句话）

返回 JSON 数组格式。只返回 JSON，不要其他内容。

文档路径：{file_path.name}"""

    try:
        raw = _call_chat_api(
            "你是一个文档结构分析助手。分析文档模板结构，输出 JSON。",
            prompt,
        )
        # 尝试解析 JSON
        import re
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            sections = json.loads(m.group())
            if isinstance(sections, list) and len(sections) > 0:
                return {
                    "name": f"导入模板-{file_path.stem}",
                    "sections": sections,
                }
    except Exception:
        pass
    return None
