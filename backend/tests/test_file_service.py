import pytest

from app.services.file_service import FileService


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
