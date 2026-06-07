"""
V2 智能命名 - 支持 OpenAI / DeepSeek / Kimi

针对大学生场景优化：
- 提取文件内容供 AI 分析
- 识别简历、作业、论文、策划案、议程、活动总结等文档类型
- 从内容中提取标题、落款时间和落款/作者信息
- 文件名格式：YYYY年M月D日-文档类型-标题.扩展名
- 文档类型同时用作 output 子文件夹分类
"""

import json
import logging
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from config import (
    get_ai_api_key,
    get_api_base_url,
    get_api_model,
    get_api_key_hint,
    get_provider_label,
)
from content_extractor import ContentPreview, extract_content_preview
from naming import WINDOWS_INVALID_CHARS
from notify import show_warning

# ── 文档类型定义（大学生场景，也是 output 子文件夹名）─────────

COLLEGE_DOC_TYPES = [
    "简历",
    "作业",
    "论文",
    "策划案",
    "方案",
    "议程",
    "会议纪要",
    "活动总结",
    "报告",
    "申请书",
    "通知",
    "证明",
    "笔记",
    "其他文档",
]

# ── 日期格式化 ──────────────────────────────────────────────

def _format_date_cn(dt: datetime) -> str:
    """中文日期格式：2026年6月7日（无前导零）"""
    return f"{dt.year}年{dt.month}月{dt.day}日"


def _parse_date_str(date_str: str) -> str:
    """
    解析 AI 返回的日期字符串，统一转为「年月日」中文格式。
    支持：2026-06-07 / 2026年6月7日 / 2026/06/07 / 2026.06.07
    解析失败返回空字符串。
    """
    date_str = date_str.strip()
    if not date_str:
        return ""

    patterns = [
        r"(\d{4})[年/\-.](\d{1,2})[月/\-.](\d{1,2})[日]?",
        r"(\d{4})[年/\-.](\d{1,2})[月](\d{1,2})[日]?",
    ]
    for pat in patterns:
        m = re.search(pat, date_str)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = datetime(y, mo, d)
                return _format_date_cn(dt)
            except ValueError:
                return ""
    return ""


# ── Prompt 模板 ────────────────────────────────────────────

SYSTEM_PROMPT = """你是一个帮助大学生整理文件的智能助手。请根据文件名和内容片段完成以下任务：

## 任务
1. **文档类型**：从下列分类中选择最匹配的一个
   简历、作业、论文、策划案、方案、议程、会议纪要、活动总结、报告、申请书、通知、证明、笔记、其他文档

2. **文档标题**：从内容开头提取，控制在 15 字以内，保留核心主题
   - 优先用文档内的真实标题（通常在开头几行、加粗或居中）
   - 如"关于举办2026年元旦晚会的策划方案" → "元旦晚会策划"
   - 如无明确标题，根据内容概括一个简洁主题

3. **落款日期**：从内容末尾提取文档的落款日期/签署日期
   - 格式必须为 YYYY-MM-DD（如 2026-01-01）
   - 如果找不到落款日期，返回空字符串 ""

4. **作者/落款组织**：从内容末尾提取（可选）
   - 个人姓名或组织名称
   - 找不到则为空字符串

## 输出格式（必须是合法 JSON，不要输出任何其他内容）
{"doc_type": "文档类型", "title": "文档标题（15字内）", "doc_date": "YYYY-MM-DD或空", "author": "作者或组织名"}

## 示例
文件"元旦晚会策划.docx"，内容开头"2026年元旦联欢晚会活动策划方案"，末尾"校学生会文艺部 2025年12月15日"
→ {"doc_type": "策划案", "title": "元旦联欢晚会策划", "doc_date": "2025-12-15", "author": "校学生会文艺部"}

文件"张三简历.docx"，内容开头"个人简历\n张三\n求职意向：软件开发"
→ {"doc_type": "简历", "title": "张三个人简历", "doc_date": "", "author": "张三"}

文件"IMG_001.jpg"（无内容可提取）
→ {"doc_type": "其他文档", "title": "手机拍摄照片", "doc_date": "", "author": ""}

文件"物理实验报告.pdf"，内容开头"实验报告\n题目：密立根油滴实验"，末尾"姓名：李四 2026年3月1日"
→ {"doc_type": "报告", "title": "密立根油滴实验报告", "doc_date": "2026-03-01", "author": "李四"}"""

USER_PROMPT_TEMPLATE = """请分析以下文件：

文件名：{original_name}
扩展名：{extension}

{content_context}"""


def _build_user_prompt(
    file_path: Path,
    content_preview: ContentPreview | None = None,
) -> str:
    """构建发送给 AI 的用户消息"""
    context = content_preview.ai_context if content_preview else ""
    if not context:
        context = "（无法提取文件内容，仅根据文件名判断）"

    return USER_PROMPT_TEMPLATE.format(
        original_name=file_path.name,
        extension=file_path.suffix.lower(),
        content_context=context,
    )


# ── API 调用 ───────────────────────────────────────────────

def _call_chat_api(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    max_retries: int = 3,
) -> str:
    """调用 OpenAI 兼容接口，返回 AI 响应文本"""
    url = f"{get_api_base_url()}/chat/completions"
    payload = {
        "model": get_api_model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))

            content = body["choices"][0]["message"]["content"]
            return content.strip()

        except urllib.error.HTTPError as error:
            if 400 <= error.code < 500 and error.code != 429:
                if error.code == 400:
                    payload.pop("response_format", None)
                else:
                    raise
            last_error = error
            if attempt < max_retries:
                wait = 2 ** attempt
                logging.warning(
                    "API 请求失败 (%s)，%ds 后重试 (%d/%d)",
                    error.code, wait, attempt, max_retries,
                )
                time.sleep(wait)

        except (urllib.error.URLError, OSError) as error:
            last_error = error
            if attempt < max_retries:
                wait = 2 ** attempt
                logging.warning(
                    "网络错误，%ds 后重试 (%d/%d): %s",
                    wait, attempt, max_retries, error,
                )
                time.sleep(wait)

    raise last_error


# ── AI 响应解析 ────────────────────────────────────────────

def _parse_ai_response(raw: str) -> dict:
    """
    解析 AI 返回的 JSON。失败返回空 dict。
    """
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "doc_type" in data:
            return data
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and "doc_type" in data:
                return data
        except json.JSONDecodeError:
            pass

    logging.warning("AI 返回非 JSON 格式: %s", raw[:100])
    return {}


def _validate_doc_type(doc_type: str) -> str:
    """校验文档类型，不在列表中的回退为「其他文档」"""
    doc_type = doc_type.strip()
    if doc_type in COLLEGE_DOC_TYPES:
        return doc_type
    for valid_type in COLLEGE_DOC_TYPES:
        if valid_type in doc_type or doc_type in valid_type:
            return valid_type
    logging.warning("AI 返回未知文档类型 '%s'，回退为「其他文档」", doc_type)
    return "其他文档"


def _sanitize_text(text: str, max_len: int = 20) -> str:
    """清洗文本：去空格、去非法字符、限长"""
    text = text.strip()
    for char in WINDOWS_INVALID_CHARS:
        text = text.replace(char, "")
    text = re.sub(r"\s+", "", text)
    if len(text) > max_len:
        text = text[:max_len]
    return text


# ── 文件名组装 ─────────────────────────────────────────────

def _assemble_filename(
    doc_type: str,
    title: str,
    file_path: Path,
    date_str: str,
) -> str:
    """
    组装最终文件名：日期-文档类型-标题.扩展名
    格式示例：2026年6月7日-活动方案-元旦晚会.docx
    """
    extension = file_path.suffix.lower()
    title = _sanitize_text(title, max_len=20)

    if not title:
        title = file_path.stem.strip() or "文件"

    return f"{date_str}-{doc_type}-{title}{extension}"


# ── 主入口 ─────────────────────────────────────────────────

def generate_ai_filename(file_path: Path, category_hint: str = "其他") -> dict | None:
    """
    主入口：提取文件内容 → 调用 AI → 解析 JSON → 组装文件名

    返回 dict：
        {"filename": str, "doc_type": str, "doc_date": str}
    失败返回 None，由调用方回退到 V1 规则命名。
    """
    api_key = get_ai_api_key()
    if not api_key:
        logging.warning(get_api_key_hint())
        return None

    provider = get_provider_label()

    try:
        # 1. 提取文件内容
        content_preview = extract_content_preview(file_path)

        # 2. 调用 AI
        user_prompt = _build_user_prompt(file_path, content_preview)
        raw_response = _call_chat_api(SYSTEM_PROMPT, user_prompt, api_key)

        # 3. 解析 JSON
        parsed = _parse_ai_response(raw_response)

        if not parsed:
            return None

        # 4. 提取字段
        doc_type = _validate_doc_type(parsed.get("doc_type", "其他文档"))
        title = parsed.get("title", "").strip()
        ai_doc_date = parsed.get("doc_date", "").strip()

        # 5. 确定日期：落款时间 > 文件修改时间
        doc_date_cn = _parse_date_str(ai_doc_date)
        if not doc_date_cn:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            doc_date_cn = _format_date_cn(mtime)

        # 6. 组装文件名
        filename = _assemble_filename(doc_type, title, file_path, doc_date_cn)

        logging.info(
            "AI 命名[%s]: %s → [%s] %s",
            provider, file_path.name, doc_type, filename,
        )

        # 7. 同时返回 doc_type（作为 output 子文件夹名）和 doc_date
        return {
            "filename": filename,
            "doc_type": doc_type,
            "doc_date": doc_date_cn,
        }

    except urllib.error.HTTPError as error:
        detail = ""
        try:
            detail = error.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        logging.warning("AI 命名 API 错误 [%s] (%s): %s", provider, error.code, detail[:200])

        if error.code == 401 or error.code == 403:
            show_warning(
                "AI 配置错误",
                f"API Key 无效或已过期。\n\n请在托盘菜单「配置 AI」中重新设置。\n当前平台：{provider}",
                error_key="ai_auth_error",
            )
        elif error.code == 429:
            show_warning(
                "AI 请求过于频繁",
                "API 请求被限流，稍后会自动恢复。\n文件将以基础命名模式归档。",
                error_key="ai_rate_limit",
            )
        else:
            show_warning(
                "AI 服务异常",
                f"AI 命名暂时不可用（{error.code}），已自动切换为基础命名。\n\n不影响文件归档，只是命名不带 AI 智能识别。",
                error_key="ai_service_error",
            )
        return None
    except Exception as error:
        logging.warning("AI 命名失败 [%s]: %s", provider, error)
        show_warning(
            "AI 服务连接失败",
            "无法连接 AI 服务，已自动切换为基础命名。\n\n请检查网络连接。文件仍会正常归档。",
            error_key="ai_connection_error",
        )
        return None
