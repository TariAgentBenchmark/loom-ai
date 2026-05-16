from types import SimpleNamespace

import pytest

from app.models.task import TaskType
from app.services.processing_service import ProcessingService
from app.utils.result_previews import (
    get_result_preview_urls,
    with_result_previews,
)


def test_result_preview_metadata_preserves_index_order():
    metadata = with_result_previews(
        {"processing_token": "abc"},
        ["results/a.png", "", "results/c.png"],
        ["a.png", "", "c.png"],
    )

    assert metadata["processing_token"] == "abc"
    assert get_result_preview_urls(metadata, expected_count=4) == [
        "results/a.png",
        "",
        "results/c.png",
        "",
    ]


@pytest.mark.asyncio
async def test_vector_eps_result_gets_png_preview():
    service = ProcessingService()
    calls = {}

    class FakeFileService:
        async def create_eps_preview(self, eps_bytes):
            calls["eps_bytes"] = eps_bytes
            return b"png-bytes"

        async def save_upload_file(
            self,
            file_bytes,
            filename,
            subfolder,
            validate_dimensions=True,
            validate_file_size=True,
        ):
            calls["saved"] = {
                "file_bytes": file_bytes,
                "filename": filename,
                "subfolder": subfolder,
                "validate_dimensions": validate_dimensions,
                "validate_file_size": validate_file_size,
            }
            return "results/preview_task_vectorize_abc_0.png"

    service.file_service = FakeFileService()
    service._log_task_event = lambda *args, **kwargs: None
    task = SimpleNamespace(
        type=TaskType.VECTORIZE.value,
        task_id="task_vectorize_abc",
    )

    preview_url, preview_filename = await service._maybe_create_result_preview(
        None,
        task,
        result_index=0,
        result_url="results/result.eps",
        result_filename="result.eps",
        result_bytes=b"%!PS-Adobe-3.0 EPSF-3.0\n",
    )

    assert preview_url == "results/preview_task_vectorize_abc_0.png"
    assert preview_filename == "preview_task_vectorize_abc_0.png"
    assert calls["eps_bytes"].startswith(b"%!PS-Adobe")
    assert calls["saved"] == {
        "file_bytes": b"png-bytes",
        "filename": "preview_task_vectorize_abc_0.png",
        "subfolder": "results",
        "validate_dimensions": False,
        "validate_file_size": False,
    }


@pytest.mark.asyncio
async def test_non_eps_vector_result_does_not_create_preview():
    service = ProcessingService()
    task = SimpleNamespace(
        type=TaskType.VECTORIZE.value,
        task_id="task_vectorize_svg",
    )

    preview_url, preview_filename = await service._maybe_create_result_preview(
        None,
        task,
        result_index=0,
        result_url="results/result.svg",
        result_filename="result.svg",
        result_bytes=b"<svg></svg>",
    )

    assert preview_url is None
    assert preview_filename is None


@pytest.mark.asyncio
async def test_completed_vector_eps_task_backfills_missing_preview_metadata():
    service = ProcessingService()
    task = SimpleNamespace(
        is_completed=True,
        result_image_url="results/result.eps",
        result_filename="result.eps",
        type=TaskType.VECTORIZE.value,
        extra_metadata={"processing_token": "abc"},
    )
    db_calls = []
    db = SimpleNamespace(
        commit=lambda: db_calls.append("commit"),
        refresh=lambda refreshed_task: db_calls.append(
            ("refresh", refreshed_task is task)
        ),
    )

    async def fake_create_preview(*args, **kwargs):
        return "results/preview_result.png", "preview_result.png"

    service._maybe_create_result_preview = fake_create_preview

    await service.ensure_result_previews(db, task)

    assert get_result_preview_urls(task.extra_metadata, expected_count=1) == [
        "results/preview_result.png"
    ]
    assert db_calls == ["commit", ("refresh", True)]
