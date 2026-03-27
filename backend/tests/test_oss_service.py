import pytest

from app.services.oss_service import oss_service


class DummyBucket:
    def __init__(self):
        self.calls = []

    def sign_url(self, method, key, expires, headers=None, params=None, slash_safe=False, additional_headers=None):
        self.calls.append(
            {
                "method": method,
                "key": key,
                "expires": expires,
                "headers": headers,
                "params": params,
                "slash_safe": slash_safe,
                "additional_headers": additional_headers,
            }
        )
        return "https://example.com/presigned"


@pytest.mark.asyncio
async def test_generate_presigned_url_preserves_path_separators(monkeypatch):
    bucket = DummyBucket()

    monkeypatch.setattr(oss_service, "auth", object())
    monkeypatch.setattr(oss_service, "bucket", bucket)
    monkeypatch.setattr(oss_service, "expiration_time", 3600)

    url = await oss_service.generate_presigned_url("uploads/2026/03/27/test.jpg")

    assert url == "https://example.com/presigned"
    assert bucket.calls == [
        {
            "method": "GET",
            "key": "uploads/2026/03/27/test.jpg",
            "expires": 3600,
            "headers": None,
            "params": None,
            "slash_safe": True,
            "additional_headers": None,
        }
    ]
