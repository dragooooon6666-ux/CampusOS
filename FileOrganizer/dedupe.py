"""
output 文件夹重复文件清理

按文件内容（MD5）比对，同一分类目录内只保留修改时间最新的一份。
"""

import hashlib
import logging
from collections import defaultdict
from pathlib import Path

from organizer import OUTPUT_DIR


def _compute_file_hash(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.md5()
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _collect_files_by_hash(folder: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)

    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue
        try:
            file_hash = _compute_file_hash(file_path)
        except OSError as error:
            logging.warning("无法读取文件，跳过: %s (%s)", file_path.name, error)
            continue
        groups[file_hash].append(file_path)

    return groups


def remove_duplicates_in_output(output_dir: Path | None = None) -> dict:
    """
    扫描 output 各分类子文件夹，删除内容重复的文件，只保留最新修改的一份。

    返回统计信息：deleted_count, kept_count, details
    """
    target_dir = output_dir or OUTPUT_DIR
    deleted_files: list[Path] = []
    kept_files: list[Path] = []
    duplicate_groups = 0

    if not target_dir.exists():
        logging.info("output 目录不存在，跳过去重。")
        return {
            "deleted_count": 0,
            "kept_count": 0,
            "duplicate_groups": 0,
            "deleted_files": [],
            "kept_files": [],
        }

    logging.info("开始一键清理 output 重复文件")

    for category_dir in sorted(target_dir.iterdir()):
        if not category_dir.is_dir():
            continue

        hash_groups = _collect_files_by_hash(category_dir)

        for files in hash_groups.values():
            if len(files) <= 1:
                continue

            duplicate_groups += 1
            newest = max(files, key=lambda path: path.stat().st_mtime)
            kept_files.append(newest)

            for file_path in files:
                if file_path == newest:
                    continue
                try:
                    file_path.unlink()
                    deleted_files.append(file_path)
                    logging.info(
                        "去重删除: %s/%s  (保留: %s)",
                        category_dir.name,
                        file_path.name,
                        newest.name,
                    )
                except OSError as error:
                    logging.warning("删除失败: %s (%s)", file_path, error)

    logging.info(
        "重复文件清理完成：删除 %d 个，保留 %d 个最新副本，涉及 %d 组重复",
        len(deleted_files),
        len(kept_files),
        duplicate_groups,
    )

    return {
        "deleted_count": len(deleted_files),
        "kept_count": len(kept_files),
        "duplicate_groups": duplicate_groups,
        "deleted_files": deleted_files,
        "kept_files": kept_files,
    }
