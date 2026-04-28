import pytest
from io import BytesIO
from PIL import Image

from app.services.file_service import FileService


def _make_image_bytes(fmt: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (12, 8), color=(12, 34, 56)).save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_ensure_preview_url_falls_back_to_original_for_large_oss_images(monkeypatch):
    service = FileService()

    async def fake_accessible_url(file_url):
        return f"accessible:{file_url}"

    async def fake_transform_safe(object_key):
        return False

    monkeypatch.setattr(service, "is_managed_oss_ref", lambda _: True)
    monkeypatch.setattr(service, "_is_preview_transform_supported", lambda _: True)
    monkeypatch.setattr(service, "extract_oss_object_key", lambda _: "results/2026/04/01/test.png")
    monkeypatch.setattr(service, "ensure_accessible_url", fake_accessible_url)
    monkeypatch.setattr(service, "_is_oss_transform_safe", fake_transform_safe)

    url = await service.ensure_preview_url("results/2026/04/01/test.png")

    assert url == "accessible:results/2026/04/01/test.png"


@pytest.mark.asyncio
async def test_ensure_preview_url_uses_oss_process_when_source_is_safe(monkeypatch):
    service = FileService()
    captured = {}

    async def fake_transform_safe(object_key):
        return True

    async def fake_generate_presigned_url(object_key, params=None, expiration=None):
        captured["object_key"] = object_key
        captured["params"] = params
        captured["expiration"] = expiration
        return "https://example.com/preview"

    monkeypatch.setattr(service, "is_managed_oss_ref", lambda _: True)
    monkeypatch.setattr(service, "_is_preview_transform_supported", lambda _: True)
    monkeypatch.setattr(service, "extract_oss_object_key", lambda _: "results/2026/04/01/test.png")
    monkeypatch.setattr(service, "_is_oss_transform_safe", fake_transform_safe)
    monkeypatch.setattr(service.oss_service, "generate_presigned_url", fake_generate_presigned_url)

    url = await service.ensure_preview_url("results/2026/04/01/test.png")

    assert url == "https://example.com/preview"
    assert captured == {
        "object_key": "results/2026/04/01/test.png",
        "params": {
            "x-oss-process": "image/resize,m_lfit,w_1600,h_1600/format,webp/quality,q_78",
        },
        "expiration": None,
    }


@pytest.mark.asyncio
async def test_save_upload_file_normalizes_png_bytes_before_oss_upload():
    service = FileService()
    uploaded = {}

    class FakeOSSService:
        def is_configured(self):
            return True

        async def upload_file(self, file_bytes, filename, prefix="uploads", content_type=None):
            uploaded["bytes"] = file_bytes
            uploaded["filename"] = filename
            uploaded["prefix"] = prefix
            return {
                "object_key": f"{prefix}/normalized.png",
                "url": "https://example.com/normalized.png",
            }

    service._oss_service = FakeOSSService()

    saved_ref = await service.save_upload_file(
        _make_image_bytes("JPEG"),
        "result.png",
        "results",
        validate_dimensions=False,
        validate_file_size=False,
    )

    assert saved_ref == "results/normalized.png"
    assert uploaded["filename"] == "result.png"
    assert uploaded["prefix"] == "results"
    assert Image.open(BytesIO(uploaded["bytes"])).format == "PNG"
