import asyncio
import logging
import os
import zipfile
from typing import AsyncIterator, Optional
from urllib.parse import urlparse

import aiofiles
import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.utils.downloads import build_download_filename, normalize_filename_for_content
from app.utils.result_filter import filter_result_lists, split_and_clean_csv

logger = logging.getLogger(__name__)

DOWNLOAD_CHUNK_SIZE = 1024 * 1024


def stream_headers(download_name: str) -> dict[str, str]:
    return {
        "Content-Disposition": f'attachment; filename="{download_name}"',
        "Cache-Control": "no-store",
        "X-Accel-Buffering": "no",
    }


def _basename_from_ref(file_ref: str) -> str:
    if not file_ref:
        return ""
    try:
        if file_ref.startswith("http"):
            return os.path.basename(urlparse(file_ref).path)
    except Exception:
        pass
    return os.path.basename(file_ref.split("?", 1)[0])


def _unique_zip_entry_name(entry_name: str, used_names: set[str]) -> str:
    candidate = entry_name or "result.png"
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    stem, suffix = os.path.splitext(candidate)
    counter = 2
    while True:
        indexed_name = f"{stem}_{counter}{suffix}"
        if indexed_name not in used_names:
            used_names.add(indexed_name)
            return indexed_name
        counter += 1


async def iter_file_chunks(
    file_service,
    file_url: str,
    chunk_size: int = DOWNLOAD_CHUNK_SIZE,
) -> AsyncIterator[bytes]:
    if file_url.startswith("/files/"):
        file_path = file_url.replace("/files/", f"{file_service.upload_path}/")
        if not os.path.exists(file_path):
            raise FileNotFoundError("文件不存在")

        async with aiofiles.open(file_path, "rb") as file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        return

    object_key = file_service.extract_oss_object_key(file_url)
    if object_key and file_service.oss_service.bucket:
        try:
            result = await asyncio.to_thread(
                file_service.oss_service.bucket.get_object,
                object_key,
            )
            try:
                while True:
                    chunk = await asyncio.to_thread(result.read, chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                close = getattr(result, "close", None)
                if close:
                    await asyncio.to_thread(close)
            return
        except Exception as exc:
            logger.error("从OSS流式读取文件失败: %s", str(exc))
            if not file_url.startswith("http"):
                raise

    if file_url.startswith("http"):
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", file_url) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size):
                    if chunk:
                        yield chunk
        return

    raise ValueError("无效的文件URL")


async def stream_single_download(file_service, file_url: str, filename_value: str):
    clean_url = file_url.strip()
    chunk_iter = iter_file_chunks(file_service, clean_url)
    try:
        first_chunk = await anext(chunk_iter)
    except StopAsyncIteration:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception:
        raise HTTPException(status_code=404, detail="文件不存在")

    filename_candidate = filename_value.strip() or _basename_from_ref(clean_url) or "result.png"
    download_name = normalize_filename_for_content(
        build_download_filename(filename_candidate),
        first_chunk,
    )

    async def body() -> AsyncIterator[bytes]:
        yield first_chunk
        async for chunk in chunk_iter:
            yield chunk

    return StreamingResponse(
        body(),
        headers=stream_headers(download_name),
        media_type="application/octet-stream",
    )


class _StreamingZipWriter:
    def __init__(self):
        self._chunks: list[bytes] = []

    def write(self, data: bytes) -> int:
        if data:
            self._chunks.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        return None

    def take_chunks(self) -> list[bytes]:
        chunks = self._chunks
        self._chunks = []
        return chunks


async def iter_streaming_zip(
    file_service,
    entries: list[tuple[str, str]],
) -> AsyncIterator[bytes]:
    writer = _StreamingZipWriter()
    used_names: set[str] = set()
    with zipfile.ZipFile(writer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for index, (file_url, filename_value) in enumerate(entries):
            clean_url = file_url.strip()
            if not clean_url:
                continue

            chunk_iter = iter_file_chunks(file_service, clean_url)
            try:
                first_chunk = await anext(chunk_iter)
            except StopAsyncIteration:
                continue
            except Exception as exc:
                logger.warning("流式打包结果文件失败(%s): %s", clean_url, exc)
                continue

            fallback_name = (
                _basename_from_ref(filename_value.strip())
                or _basename_from_ref(clean_url)
                or f"result_{index + 1}.png"
            )
            entry_name = _unique_zip_entry_name(
                normalize_filename_for_content(fallback_name, first_chunk),
                used_names,
            )

            with zip_file.open(entry_name, "w") as entry_file:
                entry_file.write(first_chunk)
                for zip_chunk in writer.take_chunks():
                    yield zip_chunk

                async for chunk in chunk_iter:
                    entry_file.write(chunk)
                    for zip_chunk in writer.take_chunks():
                        yield zip_chunk

            for zip_chunk in writer.take_chunks():
                yield zip_chunk

    for zip_chunk in writer.take_chunks():
        yield zip_chunk


def select_task_download_entries(
    task,
    file_type: str = "result",
    file_index: Optional[int] = None,
) -> list[tuple[str, str]]:
    if file_type == "original":
        if not task.original_image_url:
            raise HTTPException(status_code=404, detail="原图文件不存在")
        if file_index not in (None, 0):
            raise HTTPException(status_code=400, detail="无效的文件索引")
        return [(task.original_image_url, task.original_filename or "")]

    if file_type != "result":
        raise HTTPException(status_code=400, detail="无效的文件类型")

    if not task.result_image_url:
        raise HTTPException(status_code=404, detail="结果文件不存在")

    file_urls = split_and_clean_csv(task.result_image_url)
    filenames = split_and_clean_csv(task.result_filename)
    filtered_urls, filtered_filenames = filter_result_lists(
        task.type,
        file_urls,
        filenames,
    )

    if not filtered_urls:
        raise HTTPException(status_code=404, detail="结果文件不存在")

    if file_index is not None:
        if file_index < 0 or file_index >= len(filtered_urls):
            raise HTTPException(status_code=400, detail="无效的文件索引")

        filename_value = ""
        if filtered_filenames and file_index < len(filtered_filenames):
            filename_value = filtered_filenames[file_index]
        elif len(filtered_urls) == 1 and task.result_filename:
            filename_value = task.result_filename
        return [(filtered_urls[file_index], filename_value)]

    return [
        (
            file_url,
            filtered_filenames[index]
            if filtered_filenames and index < len(filtered_filenames)
            else (task.result_filename if len(filtered_urls) == 1 else ""),
        )
        for index, file_url in enumerate(filtered_urls)
    ]


async def build_download_response(
    file_service,
    entries: list[tuple[str, str]],
):
    if not entries:
        raise HTTPException(status_code=404, detail="结果文件不存在")

    if len(entries) == 1:
        file_url, filename_value = entries[0]
        return await stream_single_download(file_service, file_url, filename_value)

    download_name = build_download_filename(None, "zip")
    return StreamingResponse(
        iter_streaming_zip(file_service, entries),
        headers=stream_headers(download_name),
        media_type="application/zip",
    )


async def build_task_download_response(
    task,
    file_service,
    file_type: str = "result",
    file_index: Optional[int] = None,
):
    entries = select_task_download_entries(task, file_type, file_index)
    return await build_download_response(file_service, entries)
