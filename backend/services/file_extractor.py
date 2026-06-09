"""
文件提取器 — 文件夹递归 + 压缩包解压 + 媒体文件处理
"""

import shutil
import tempfile
import zipfile
from pathlib import Path

SUPPORTED_ARCHIVES = {".zip"}


def extract_folder(folder_path: Path, dest_dir: Path) -> list[Path]:
    """递归扫描文件夹，将所有文件复制到目标目录。返回文件路径列表。"""
    files = []
    for item in folder_path.rglob("*"):
        if item.is_file():
            # 保持相对路径防重名
            rel = item.relative_to(folder_path)
            dest = dest_dir / rel.name
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{rel.stem}({counter}){rel.suffix}"
                counter += 1
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            files.append(dest)
    return files


def extract_archive(archive_path: Path, dest_dir: Path) -> list[Path]:
    """解压压缩包到目标目录，返回文件路径列表。"""
    ext = archive_path.suffix.lower()
    if ext not in SUPPORTED_ARCHIVES:
        raise ValueError(f"不支持的压缩格式: {ext}")

    files = []
    if ext == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.namelist():
                # 跳过目录条目
                if member.endswith("/"):
                    continue
                # 安全路径：防止路径穿越
                safe_name = Path(member).name
                dest = dest_dir / safe_name
                counter = 1
                while dest.exists():
                    dest = dest_dir / f"{Path(safe_name).stem}({counter}){Path(safe_name).suffix}"
                    counter += 1
                with zf.open(member) as src:
                    dest.write_bytes(src.read())
                files.append(dest)
    return files


def process_entry(path: Path, input_dir: Path) -> dict:
    """
    处理任意入口（文件/文件夹/压缩包），返回：
    {"type": "file"|"folder"|"archive", "files": [...], "message": str}
    """
    result = {"type": "file", "files": [], "message": ""}

    if path.is_file():
        ext = path.suffix.lower()
        if ext in SUPPORTED_ARCHIVES:
            files = extract_archive(path, input_dir)
            result["type"] = "archive"
            result["files"] = files
            result["message"] = f"已从压缩包解压 {len(files)} 个文件"
        else:
            dest = input_dir / path.name
            counter = 1
            while dest.exists():
                dest = input_dir / f"{path.stem}({counter}){path.suffix}"
                counter += 1
            shutil.copy2(path, dest)
            result["files"] = [dest]
            result["message"] = "1 个文件"

    elif path.is_dir():
        files = extract_folder(path, input_dir)
        result["type"] = "folder"
        result["files"] = files
        result["message"] = f"已从文件夹提取 {len(files)} 个文件"

    return result
