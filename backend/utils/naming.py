"""V1 规则命名 + 扩展名分类（AI 不可用时的回退方案）"""

from pathlib import Path

EXTENSION_CATEGORY = {
    ".doc": "Word文档", ".docx": "Word文档",
    ".xls": "Excel表格", ".xlsx": "Excel表格", ".csv": "Excel表格",
    ".pdf": "PDF文档",
    ".jpg": "图片", ".jpeg": "图片", ".png": "图片", ".gif": "图片",
    ".bmp": "图片", ".webp": "图片",
    ".mp4": "视频", ".avi": "视频", ".mov": "视频", ".mkv": "视频",
    ".zip": "压缩包", ".rar": "压缩包", ".7z": "压缩包",
    ".pptx": "PPT演示", ".ppt": "PPT演示",
    ".txt": "纯文本", ".md": "纯文本",
}

NON_TEXT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
    ".mp3", ".wav", ".flac", ".aac", ".ogg",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".exe", ".dll", ".bin", ".iso",
}


def get_file_category_label(file_path: Path) -> str:
    """根据扩展名获取 V1 分类标签（非文本回退用）"""
    return EXTENSION_CATEGORY.get(file_path.suffix.lower(), "其他文件")
