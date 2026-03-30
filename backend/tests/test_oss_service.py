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
    monkeypatch.setattr(oss_service, "bucket_domain", "")
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


@pytest.mark.asyncio
async def test_generate_presigned_url_uses_custom_domain_when_configured(monkeypatch):
    bucket = DummyBucket()
    created = {}

    def fake_bucket(auth, endpoint, bucket_name, is_cname=False, **kwargs):
        created["auth"] = auth
        created["endpoint"] = endpoint
        created["bucket_name"] = bucket_name
        created["is_cname"] = is_cname
        created["kwargs"] = kwargs
        return bucket

    monkeypatch.setattr("app.services.oss_service.oss2.Bucket", fake_bucket)
    monkeypatch.setattr(oss_service, "auth", object())
    monkeypatch.setattr(oss_service, "bucket", object())
    monkeypatch.setattr(oss_service, "bucket_name", "loomai")
    monkeypatch.setattr(oss_service, "bucket_domain", "oss.tuyunai.cn")
    monkeypatch.setattr(oss_service, "expiration_time", 600)

    url = await oss_service.generate_presigned_url("results/2026/03/29/test.png")

    assert url == "https://example.com/presigned"
    assert created == {
        "auth": oss_service.auth,
        "endpoint": "https://oss.tuyunai.cn",
        "bucket_name": "loomai",
        "is_cname": True,
        "kwargs": {},
    }
    assert bucket.calls == [
        {
            "method": "GET",
            "key": "results/2026/03/29/test.png",
            "expires": 600,
            "headers": None,
            "params": None,
            "slash_safe": True,
            "additional_headers": None,
        }
    ]


def test_build_file_url_uses_normalized_bucket_domain(monkeypatch):
    monkeypatch.setattr(oss_service, "bucket_domain", "https://oss.tuyunai.cn/")

    url = oss_service._build_file_url("uploads/2026/03/30/test.webp")

    assert url == "https://oss.tuyunai.cn/uploads/2026/03/30/test.webp"
