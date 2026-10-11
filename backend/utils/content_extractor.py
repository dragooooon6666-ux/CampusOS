"""
文件内容提取模块

支持：docx / pdf / xlsx / pptx / txt / md / 纯文本
"""

import re
from pathlib import Path

# ── 提取结果 ──────────────────────────────────────────────

MAX_PREVIEW_CHARS = 800
TITLE_LINES = 6
SIGNATURE_LINES = 4


class ContentPreview:
    """提取后的内容预览，包含标题区和落款区"""

    def __init__(self, title_section: str = "", signature_section: str = ""):
        self.title_section = title_section
        self.signature_section = signature_section
        self.full_text = ""

    @property
    def ai_context(self) -> str:
        parts = []
        if self.title_section:
            parts.append(f"【文件开头内容】\n{self.title_section}")
        if self.signature_section:
            parts.append(f"【文件末尾内容（落款/署名）】\n{self.signature_section}")
        return "\n\n".join(parts) if parts else ""

    def __bool__(self):
        return bool(self.ai_context)


# ── 各类型提取器 ───────────────────────────────────────────

def _extract_docx(file_path: Path) -> ContentPreview:
    import docx
    doc = docx.Document(str(file_path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        return ContentPreview()
    return _build_preview(paragraphs)


def _extract_pdf(file_path: Path) -> ContentPreview:
    from PyPDF2 import PdfReader
    reader = PdfReader(str(file_path))
    all_lines: list[str] = []
    for page in reader.pages[:3]:
        text = page.extract_text()
        if text:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            all_lines.extend(lines)
        if sum(len(l) for l in all_lines) > MAX_PREVIEW_CHARS * 2:
            break
    if not all_lines:
        return ContentPreview()
    return _build_preview(all_lines)


def _extract_xlsx(file_path: Path) -> ContentPreview:
    from openpyxl import load_workbook
    wb = load_workbook(str(file_path), read_only=True, data_only=True)
    lines: list[str] = []
    for sheet_name in wb.sheetnames[:2]:
        ws = wb[sheet_name]
        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx > 20:
                break
            row_text = " ".join(str(c) for c in row if c is not None).strip()
            if row_text:
                lines.append(row_text)
    wb.close()
    return _build_preview(lines)


def _extract_pptx(file_path: Path) -> ContentPreview:
    """从 PowerPoint 提取幻灯片文本"""
    from pptx import Presentation
    prs = Presentation(str(file_path))
    all_lines: list[str] = []

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        all_lines.append(text)
        if sum(len(l) for l in all_lines) > MAX_PREVIEW_CHARS * 2:
            break

    if not all_lines:
        return ContentPreview()
    return _build_preview(all_lines)


def _extract_plain(file_path: Path) -> ContentPreview:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = file_path.read_text(encoding="gbk")
        except UnicodeDecodeError:
            return ContentPreview()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return _build_preview(lines)


def _extract_nothing(file_path: Path) -> ContentPreview:
    return ContentPreview()


# ── 通用构建 ───────────────────────────────────────────────

def _build_preview(lines: list[str]) -> ContentPreview:
    if not lines:
        return ContentPreview()

    preview = ContentPreview()

    title_chars = 0
    title_lines = []
    for line in lines[:TITLE_LINES]:
        title_lines.append(line)
        title_chars += len(line)
        if title_chars >= MAX_PREVIEW_CHARS // 2:
            break
    preview.title_section = "\n".join(title_lines)[:MAX_PREVIEW_CHARS]

    if len(lines) > TITLE_LINES + 2:
        sig = lines[-SIGNATURE_LINES:]
        preview.signature_section = "\n".join(sig)[:MAX_PREVIEW_CHARS // 2]

    preview.full_text = "\n".join(lines)
    return preview


# ── 文件名类型检测 ──────────────────────────────────────────
#
# 关键词规则统一由 backend/utils/rule_classifier.py 维护：
# 那里按文件族（文稿/表格/演示）分表，并做文种结尾优先匹配。


def detect_type_from_filename(filename: str) -> str | None:
    """从文件名检测文档类型，返回类型或 None。

    复用规则分类引擎；只有中高置信度才返回，避免把误判当成结论。
    """
    from backend.utils.rule_classifier import classify

    result = classify(filename)
    if result.confidence in ("high", "medium"):
        return result.doc_type
    return None


# ── 类型 → 提取器映射 ──────────────────────────────────────

EXTRACTOR_MAP = {
    ".docx": _extract_docx,
    ".doc": _extract_docx,
    ".pdf": _extract_pdf,
    ".xlsx": _extract_xlsx,
    ".xls": _extract_xlsx,
    ".csv": _extract_plain,
    ".pptx": _extract_pptx,
    ".ppt": _extract_pptx,
    ".txt": _extract_plain,
    ".md": _extract_plain,
    ".markdown": _extract_plain,
    ".log": _extract_plain,
}

FALLBACK_EXTRACTOR = _extract_nothing


# ── 公开 API ───────────────────────────────────────────────

def extract_content_preview(file_path: Path) -> ContentPreview:
    """提取文件内容预览，包含标题区和落款区。"""
    extension = file_path.suffix.lower()
    extractor = EXTRACTOR_MAP.get(extension, FALLBACK_EXTRACTOR)

    try:
        preview = extractor(file_path)
    except Exception:
        preview = ContentPreview()

    # 文件名作为强信号 fallback
    if not preview.ai_context:
        stem = file_path.stem.strip()
        if stem and len(stem) >= 2:
            preview.title_section = f"（文件名为：{stem}）"

    return preview
