"""
AI 写作引擎 — 引导式生成 + 段落重生成
"""

import json
import logging
import re
import time
import urllib.error
import urllib.request

from backend.config import get_api_key, get_api_base_url, get_api_model, get_provider_info

logger = logging.getLogger(__name__)

WRITING_SYSTEM = """你是一个高校公文写作助手。请根据用户提供的信息和模板要求，生成规范的公文文档。

要求：
- 语言正式、客观、简洁
- 符合高校行政公文风格
- 按模板的章节结构组织内容
- 每个章节用 ## 标题标记
- 不需要的章节留空即可
- 只输出文档正文，不要额外说明"""


def _call_ai(system: str, user: str, temperature: float = 0.7) -> str:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("未配置 AI API Key")

    url = f"{get_api_base_url()}/chat/completions"
    payload = {
        "model": get_api_model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }

    for attempt in range(1, 3):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def generate_document(doc_type: str, form_data: dict, template_id: int | None = None) -> dict:
    """
    根据文档类型 + 用户输入 + 模板，生成完整文档。

    返回：{"title": str, "content": str, "provider": str}
    """
    from backend.services.template_service import get_template

    # 获取模板 sections
    if template_id:
        tmpl = get_template(template_id)
        sections = json.loads(tmpl["sections"]) if tmpl else _default_sections(doc_type)
    else:
        sections = _default_sections(doc_type)

    # 组装用户信息
    info_lines = [f"文档类型：{doc_type}"]
    for key, value in form_data.items():
        if value.strip():
            info_lines.append(f"{key}: {value.strip()}")
    user_info = "\n".join(info_lines)

    # 构建模板要求
    section_reqs = "\n".join(
        f"- {s['label']}：{s['ai_role']}" for s in sections
    )

    prompt = f"""请根据以下信息生成一份{doc_type}。

【基本信息】
{user_info}

【章节要求】（按此结构组织，每章用 ## 标题）
{section_reqs}"""

    content = _call_ai(WRITING_SYSTEM, prompt)
    title = _extract_title(content, doc_type, form_data)

    return {
        "title": title,
        "content": content,
        "provider": get_provider_info()["label"],
    }


def regenerate_section(doc_type: str, current_content: str, section_key: str,
                       section_label: str, feedback: str = "") -> str:
    """重新生成文档中的某一章节"""
    prompt = f"""以下是一份{doc_type}的当前内容。请重新生成其中的「{section_label}」章节。

【当前文档】
{current_content}

【修改要求】
{feedback if feedback else '请改进该章节，使其更详细、更专业'}"""

    return _call_ai(WRITING_SYSTEM, prompt, temperature=0.8)


def _default_sections(doc_type: str) -> list[dict]:
    defaults = {
        "新闻稿": [
            {"key": "title", "label": "标题", "ai_role": "提炼核心事件"},
            {"key": "lead", "label": "导语", "ai_role": "5W1H概括"},
            {"key": "process", "label": "活动过程", "ai_role": "按时间线展开"},
            {"key": "outcome", "label": "成果意义", "ai_role": "总结成果和意义"},
        ],
        "活动总结": [
            {"key": "background", "label": "活动背景", "ai_role": "简述目的和背景"},
            {"key": "process", "label": "活动开展", "ai_role": "描述过程和亮点"},
            {"key": "outcome", "label": "活动成果", "ai_role": "总结成果和数据"},
            {"key": "issues", "label": "存在问题", "ai_role": "客观分析不足"},
            {"key": "improve", "label": "改进方向", "ai_role": "提出改进建议"},
        ],
        "会议纪要": [
            {"key": "info", "label": "基本信息", "ai_role": "时间地点参会人员"},
            {"key": "agenda", "label": "会议议题", "ai_role": "列出讨论议题"},
            {"key": "discussion", "label": "讨论内容", "ai_role": "记录主要发言"},
            {"key": "decisions", "label": "决议事项", "ai_role": "列出达成的决议"},
        ],
        "通知": [
            {"key": "title", "label": "标题", "ai_role": "关于xxx的通知"},
            {"key": "body", "label": "正文", "ai_role": "通知的具体内容"},
            {"key": "requirements", "label": "具体要求", "ai_role": "列出需要执行的事项"},
        ],
    }
    return defaults.get(doc_type, [
        {"key": "title", "label": "标题", "ai_role": "文档标题"},
        {"key": "body", "label": "正文", "ai_role": "文档正文内容"},
    ])


def _extract_title(content: str, doc_type: str, form_data: dict) -> str:
    """从生成内容中提取标题"""
    # 优先用 ## 标题行
    m = re.search(r'^##\s*(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # 其次用第一行
    first_line = content.split('\n')[0].strip()
    if first_line and len(first_line) < 40:
        return first_line
    # 回退：用表单中的名称
    for key in ("event_name", "meeting_name", "title", "project_name"):
        if form_data.get(key, "").strip():
            return f"{form_data[key].strip()}{doc_type}"
    return doc_type
