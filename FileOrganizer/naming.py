"""
自动文件命名系统

- V1：纯规则命名（默认，无需 API）
- V2：AI 智能命名（config.AI_MODE = True 时启用，失败自动回退 V1）

generate_new_filename 返回 (filename, category) 元组
- category 在 AI 模式下为文档内容类型（简历/作业/论文...）
- category 在 V1 模式下为文件扩展名类型（Word/Excel/PDF...）
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import config

# 分类 -> 文件名中的类型标签
CATEGORY_LABEL_MAP = {
    "Word": "Word文档",
    "Excel": "Excel表格",
    "PDF": "PDF文档",
    "图片": "图片",
    "视频": "视频",
    "压缩包": "压缩包",
    "其他": "文件",
}

# 文件扩展名 → 分类（V1 回退用）
EXTENSION_CATEGORY_MAP = {
    ".doc": "Word",
    ".docx": "Word",
    ".xls": "Excel",
    ".xlsx": "Excel",
    ".csv": "Excel",
    ".pdf": "PDF",
    ".jpg": "图片",
    ".jpeg": "图片",
    ".png": "图片",
    ".gif": "图片",
    ".bmp": "图片",
    ".webp": "图片",
    ".mp4": "视频",
    ".avi": "视频",
    ".mov": "视频",
    ".mkv": "视频",
    ".wmv": "视频",
    ".zip": "压缩包",
    ".rar": "压缩包",
    ".7z": "压缩包",
    ".tar": "压缩包",
    ".gz": "压缩包",
}

# V1：需去掉的无意义前缀（不区分大小写）
MEANINGLESS_PREFIXES = (
    "screenshot",
    "screen shot",
    "snapshot",
    "document",
    "image",
    "photo",
    "picture",
    "scan",
    "copy",
    "file",
    "img",
    "dsc",
    "snap",
    "pic",
    "新建",
    "未命名",
)

WINDOWS_INVALID_CHARS = r'<>:"/\|?*'

# 这些文件类型无法提取文本内容，直接走 V1 扩展名分类（省 API 调用也更准确）
NON_TEXT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
    ".mp3", ".wav", ".flac", ".aac", ".ogg",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".exe", ".dll", ".bin", ".iso",
}


# ── 日期 ──────────────────────────────────────────────────

def _format_date_cn(dt: datetime) -> str:
    """中文日期格式：2026年6月7日（无前导零）"""
    return f"{dt.year}年{dt.month}月{dt.day}日"


def get_file_date(file_path: Path) -> str:
    """优先文件修改时间，失败则取当前时间，返回中文日期格式。"""
    try:
        timestamp = file_path.stat().st_mtime
        return _format_date_cn(datetime.fromtimestamp(timestamp))
    except OSError:
        return _format_date_cn(datetime.now())


def get_file_extension_category(file_path: Path) -> str:
    """根据扩展名获取 V1 分类（用于回退）。"""
    extension = file_path.suffix.lower()
    return EXTENSION_CATEGORY_MAP.get(extension, "其他")


# ── 关键词提取 ────────────────────────────────────────────

def _sanitize_keyword(keyword: str) -> str:
    for char in WINDOWS_INVALID_CHARS:
        keyword = keyword.replace(char, "")
    return keyword.strip()


def extract_keyword(stem: str) -> str:
    """
    V1 关键词提取：从原文件名提取有意义字符。
    - 英文单词保留完整长度（最多 15 字符）
    - 中文保留前 6 个字
    - 前缀剥离后若为空则保留原文
    """
    name = stem.strip()
    if not name:
        return "文件"

    original = name
    name = name.replace("_", " ").replace("-", " ")

    for prefix in sorted(MEANINGLESS_PREFIXES, key=len, reverse=True):
        pattern = rf"^{re.escape(prefix)}[\s_\d]*"
        name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()

    name = re.sub(r"^[\d\s]+", "", name).strip()

    # 剥离后为空 → 回退到原文
    if not name:
        name = original.replace("_", " ").replace("-", " ")
        name = re.sub(r"^[\d\s]+", "", name).strip()

    meaningful = re.sub(r"[^\w一-鿿]", "", name, flags=re.UNICODE)
    meaningful = _sanitize_keyword(meaningful)

    if len(meaningful) < 2:
        meaningful = re.sub(r"[^\w一-鿿]", "", original, flags=re.UNICODE)
        meaningful = _sanitize_keyword(meaningful)

    if len(meaningful) < 2:
        return "文件"

    # 中文为主：前 6 个字；英文为主：前 15 字符
    has_chinese = bool(re.search(r"[一-鿿]", meaningful))
    max_len = 6 if has_chinese else 15
    return meaningful[:max_len]


# ── V1 命名 ────────────────────────────────────────────────

def generate_v1_filename(file_path: Path, category: str) -> str:
    """
    V1 规则命名：日期-类型-关键词.扩展名
    示例：2026年6月7日-Word文档-简历初.docx
    """
    date_str = get_file_date(file_path)
    type_label = CATEGORY_LABEL_MAP.get(category, "文件")
    keyword = extract_keyword(file_path.stem)
    extension = file_path.suffix.lower()

    return f"{date_str}-{type_label}-{keyword}{extension}"


# ── 统一入口 ──────────────────────────────────────────────

def generate_new_filename(file_path: Path, category_hint: str = "") -> tuple[str, str]:
    """
    统一命名入口，返回 (filename, category) 元组。

    category 决定文件放入 output 的哪个子文件夹：
    - AI 模式：category = AI 识别的文档类型（简历/作业/论文...）
    - V1 模式：category = 文件扩展名类型（Word/Excel/PDF...）

    AI 失败时自动 fallback 到 V1。
    """
    # 确定 V1 分类（用于回退和 hint）
    ext_category = get_file_extension_category(file_path)

    # 非文本文件（图片/视频/音频/压缩包等）直接走 V1，避免浪费 API 调用
    extension = file_path.suffix.lower()
    if extension in NON_TEXT_EXTENSIONS:
        v1_filename = generate_v1_filename(file_path, ext_category)
        return (v1_filename, ext_category)

    if config.is_ai_mode_enabled():
        from ai_naming import generate_ai_filename

        result = generate_ai_filename(file_path, ext_category)
        if result:
            return (result["filename"], result["doc_type"])

        logging.warning(
            "AI 命名不可用，已回退 V1 规则命名: %s", file_path.name
        )

    # V1 回退：category 用扩展名类型
    v1_filename = generate_v1_filename(file_path, ext_category)
    return (v1_filename, ext_category)


# ── 防重名 ────────────────────────────────────────────────

def get_unique_dest_path(dest_dir: Path, new_filename: str) -> Path:
    """目标文件已存在时，追加 (1)(2)(3) 防重名。"""
    dest_path = dest_dir / new_filename
    if not dest_path.exists():
        return dest_path

    stem = Path(new_filename).stem
    suffix = Path(new_filename).suffix
    counter = 1

    while dest_path.exists():
        dest_path = dest_dir / f"{stem}({counter}){suffix}"
        counter += 1

    return dest_path
