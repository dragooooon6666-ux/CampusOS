"""非文本文件扩展名 —— 这类文件不提取内容，直接按文件名/格式分类

规则分类的完整实现见 backend/utils/rule_classifier.py
"""

NON_TEXT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
    ".mp3", ".wav", ".flac", ".aac", ".ogg",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".exe", ".dll", ".bin", ".iso",
}
