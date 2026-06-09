"""
AI 文件分析引擎 — 21 类文档分类 + 双模型支持
"""

import json
import logging
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from backend.config import get_api_key, get_api_base_url, get_api_model, get_active_provider, get_provider_info
from backend.utils.content_extractor import ContentPreview, extract_content_preview, detect_type_from_filename

logger = logging.getLogger(__name__)

# ── 22 类文档类型（4 大类 - 方案 B）────────────────────────
#
# 备用方案 A（6 组，按用途）：
#   活动文件：策划案、方案、议程、新闻稿
#   记录归档：会议纪要、活动总结、笔记
#   行政文书：通知、申请书、证明、发言稿、述职报告
#   学术文档：论文、作业、简历、报告
#   数据表格：统计表、签到表、预算表、物资清单、通讯录、排班表
#   表单模板：收集表

DOC_TYPES = [
    # 活动全流程（6）
    "策划案", "方案", "议程", "新闻稿", "活动总结", "会议纪要",
    # 办公文书（6）
    "通知", "申请书", "证明", "发言稿", "述职报告", "报告",
    # 个人信息（4）
    "简历", "作业", "论文", "笔记",
    # 数据与表单（7）
    "统计表", "签到表", "预算表", "物资清单", "通讯录", "排班表", "收集表",
    # 兜底
    "其他文档", "其他表格",
]

NON_TEXT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
    ".mp3", ".wav", ".flac", ".aac", ".ogg",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".exe", ".dll", ".bin", ".iso",
}

# ── Prompt ─────────────────────────────────────────────────

SYSTEM_PROMPT = """你是一个帮助大学生整理文件的智能助手。请根据文件名和内容片段完成以下任务。

## 任务
1. **文档类型**：从下列 4 大类中选择最匹配的一个
   - 活动全流程：策划案、方案、议程、新闻稿、活动总结、会议纪要
   - 办公文书：通知、申请书、证明、发言稿、述职报告、报告
   - 个人信息：简历、作业、论文、笔记
   - 数据与表单：统计表、签到表、预算表、物资清单、通讯录、排班表、收集表
   无法归类时使用：其他文档、其他表格

2. **文档标题**：从内容开头提取，控制在 15 字以内
   - 优先用文档内的真实标题（通常在开头几行、加粗或居中）
   - 如"关于举办2026年元旦晚会的策划方案" → "元旦晚会策划"
   - 如无明确标题，根据内容概括一个简洁主题

3. **落款日期**：从内容末尾提取文档的落款日期
   - 格式必须为 YYYY-MM-DD（如 2026-01-01）
   - 找不到落款日期返回空字符串 ""

4. **作者/落款组织**：从内容末尾提取（可选），找不到则为空字符串

## 重要规则
- **文件名优先**：如果文件名中包含明确类型关键词（如"策划书""新闻稿""预算表"），以文件名为准
- **表格识别**：内容以数字、行列结构为主 → 优先匹配表格类（预算表、统计表、签到表等）
- **收集表识别**：Word 文档中带填空式表格结构（报名表、异动表、反馈表、登记表、申报表等，以字段-填写方式呈现的单份表单）→ 分类为「收集表」
- **名单识别**：姓名罗列、人员列表 → 分类为「统计表」，不是「签到表」
- **内容稀疏时**：以文件名判断为主

## 输出格式（必须是合法 JSON）
{"doc_type": "文档类型", "title": "标题（15字内）", "doc_date": "YYYY-MM-DD或空", "author": "作者或组织名"}

## 示例
文件"元旦晚会策划.docx"，内容开头"2026年元旦联欢晚会活动策划方案"，末尾"校学生会文艺部 2025年12月15日"
→ {"doc_type": "策划案", "title": "元旦联欢晚会策划", "doc_date": "2025-12-15", "author": "校学生会文艺部"}

文件"经费预算.xlsx"，内容开头"迎新晚会经费预算 场地：2000元 设备：1500元"
→ {"doc_type": "预算表", "title": "迎新晚会经费预算", "doc_date": "", "author": ""}

文件"张三简历.docx"，内容开头"个人简历\n张三\n求职意向：软件开发"
→ {"doc_type": "简历", "title": "张三个人简历", "doc_date": "", "author": "张三"}

文件"IMG_001.jpg"（无内容可提取）
→ {"doc_type": "其他文档", "title": "手机拍摄照片", "doc_date": "", "author": ""}

文件"学籍异动表.doc"，内容为表格模板，含"姓名""学号""异动类型"等填写字段
→ {"doc_type": "收集表", "title": "学籍异动表", "doc_date": "", "author": ""}

文件"报名表.docx"，内容含"姓名""联系方式""报名项目"等填空字段
→ {"doc_type": "收集表", "title": "报名表", "doc_date": "", "author": ""}

文件"参赛人员名单.docx"，内容为姓名列表
→ {"doc_type": "统计表", "title": "参赛人员名单", "doc_date": "", "author": ""}"""

USER_PROMPT_TEMPLATE = """请分析以下文件：

文件名：{original_name}
扩展名：{extension}
{filename_hint}
{content_context}"""


def _build_user_prompt(file_path: Path, content_preview: ContentPreview | None = None) -> str:
    """构建发送给 AI 的用户消息"""
    # 文件名关键词检测
    hint = detect_type_from_filename(file_path.name)
    filename_hint = ""
    if hint:
        filename_hint = f"\n【文件名提示】文件名包含明确类型关键词，该文件很可能是「{hint}」类文档。请优先考虑此分类。"

    context = content_preview.ai_context if content_preview else ""
    if not context:
        context = "（无法提取文件内容，仅根据文件名判断）"

    return USER_PROMPT_TEMPLATE.format(
        original_name=file_path.name,
        extension=file_path.suffix.lower(),
        filename_hint=filename_hint,
        content_context=context,
    )


# ── API 调用 ───────────────────────────────────────────────

def _call_chat_api(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
    """调用 OpenAI 兼容接口"""
    api_key = get_api_key()
    if not api_key:
        raise ValueError(f"未配置 {get_provider_info()['label']} API Key")

    url = f"{get_api_base_url()}/chat/completions"
    payload = {
        "model": get_api_model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.5,
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
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
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()

        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                if e.code == 400:
                    payload.pop("response_format", None)
                else:
                    raise
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)

        except (urllib.error.URLError, OSError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    raise last_error


# ── 响应解析 ───────────────────────────────────────────────

def _parse_ai_response(raw: str) -> dict:
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "doc_type" in data:
            return data
    except json.JSONDecodeError:
        pass
    # 尝试提取 JSON 片段
    m = re.search(r'\{[^{}]*"doc_type"[^{}]*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def _validate_doc_type(doc_type: str) -> str:
    doc_type = doc_type.strip()
    if doc_type in DOC_TYPES:
        return doc_type
    for valid in DOC_TYPES:
        if valid in doc_type or doc_type in valid:
            return valid
    return "其他文档"


def _sanitize_text(text: str, max_len: int = 20) -> str:
    text = text.strip()
    for char in r'<>:"/\|?*':
        text = text.replace(char, "")
    text = re.sub(r"\s+", "", text)
    return text[:max_len] if len(text) > max_len else text


# ── 日期处理 ───────────────────────────────────────────────

def _format_date_cn(dt: datetime) -> str:
    return f"{dt.year}年{dt.month}月{dt.day}日"


def _parse_date_str(date_str: str) -> str:
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
                return _format_date_cn(datetime(y, mo, d))
            except ValueError:
                return ""
    return ""


# ── 主入口 ─────────────────────────────────────────────────

def analyze_file(file_path: Path) -> dict | None:
    """
    分析文件：提取内容 → 调 AI → 返回分类结果。

    返回：{"doc_type": str, "title": str, "doc_date": str, "author": str}
    非文本文件或 AI 不可用时返回 None。
    """
    extension = file_path.suffix.lower()

    # 媒体文件：仅根据文件名 + 扩展名分类，不调 AI 读内容
    if extension in NON_TEXT_EXTENSIONS:
        hint = detect_type_from_filename(file_path.name)
        if hint:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return {
                "doc_type": hint,
                "title": _sanitize_text(file_path.stem, max_len=20) or file_path.stem,
                "doc_date": _format_date_cn(mtime),
                "author": "",
            }
        # 完全无法识别 → 用扩展名大类
        from backend.utils.naming import get_file_category_label
        return {
            "doc_type": get_file_category_label(file_path),
            "title": file_path.stem,
            "doc_date": _format_date_cn(datetime.fromtimestamp(file_path.stat().st_mtime)),
            "author": "",
        }

    api_key = get_api_key()
    if not api_key:
        return None

    try:
        content_preview = extract_content_preview(file_path)
        user_prompt = _build_user_prompt(file_path, content_preview)
        raw = _call_chat_api(SYSTEM_PROMPT, user_prompt, max_retries=2)
        parsed = _parse_ai_response(raw)

        if not parsed:
            return None

        doc_type = _validate_doc_type(parsed.get("doc_type", "其他文档"))
        title = parsed.get("title", "").strip()
        ai_date = parsed.get("doc_date", "").strip()
        author = parsed.get("author", "").strip()

        # 文件名提示 → 直接覆盖 AI（用户规则：以文件名为准）
        filename_hint = detect_type_from_filename(file_path.name)
        if filename_hint and filename_hint != doc_type:
            doc_type = filename_hint

        doc_date_cn = _parse_date_str(ai_date)
        if not doc_date_cn:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            doc_date_cn = _format_date_cn(mtime)

        provider = get_provider_info()["label"]
        logger.info("AI[%s]: %s → [%s] %s", provider, file_path.name, doc_type, title)

        return {
            "doc_type": doc_type,
            "title": _sanitize_text(title, max_len=20),
            "doc_date": doc_date_cn,
            "author": author,
        }

    except Exception as e:
        logger.warning("AI 分析失败 [%s]: %s", file_path.name, e)
        return None
