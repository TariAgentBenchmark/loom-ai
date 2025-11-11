from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple, TypeVar

from app.models.task import TaskType

T = TypeVar("T")


def split_and_clean_csv(value: Optional[str]) -> List[str]:
    """Split a comma separated string and trim blanks."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part and part.strip()]


def determine_result_indices(task_type: str, total: int) -> List[int]:
    """
    Decide which result indices should be kept for a task.

    For seamless loop tasks, the GQCH API returns:
      0: 原图（原始参考）
      1: 接循环成品（需要的结果）
      2: 网格预览（可平铺效果）
    用户只需要第 1 张图，因此我们仅保留该索引。
    """
    if total <= 0:
        return []

    if task_type == TaskType.SEAMLESS_LOOP.value:
        return [1] if total > 1 else [0]

    return list(range(total))


def filter_items_by_indices(items: Sequence[T], indices: Sequence[int]) -> List[T]:
    """Filter a sequence by the provided indices."""
    result: List[T] = []
    for index in indices:
        if 0 <= index < len(items):
            result.append(items[index])
    return result


def filter_result_lists(
    task_type: str,
    urls: Sequence[str],
    filenames: Optional[Sequence[str]] = None,
) -> Tuple[List[str], Optional[List[str]]]:
    """Apply the task-specific filter to result URLs and filenames."""
    indices = determine_result_indices(task_type, len(urls))
    filtered_urls = filter_items_by_indices(urls, indices)
    filtered_filenames: Optional[List[str]] = None
    if filenames is not None:
        filtered_filenames = filter_items_by_indices(filenames, indices)
    return filtered_urls, filtered_filenames


def filter_result_strings(
    task_type: str,
    url_value: Optional[str],
    filename_value: Optional[str] = None,
) -> Tuple[List[str], Optional[List[str]]]:
    """Filter comma separated result strings and return the cleaned lists."""
    urls = split_and_clean_csv(url_value)
    filenames = split_and_clean_csv(filename_value) if filename_value else None
    return filter_result_lists(task_type, urls, filenames)

