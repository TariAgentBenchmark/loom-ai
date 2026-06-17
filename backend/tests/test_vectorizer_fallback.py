from contextlib import asynccontextmanager
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_client.ai_client import AIClient
from app.core.config import settings
from app.services.ai_client.a8_vectorizer_client import A8VectorizerClient
from app.services.ai_client.vectorizer_client import VectorizerClient
from app.services.ai_client.zfy_vectorizer_client import ZfyVectorizerClient
from app.services.file_service import FileService


@asynccontextmanager
async def noop_api_slot(*_args, **_kwargs):
    yield


@pytest.mark.asyncio
async def test_vectorize_image_webapi_fallback(monkeypatch):
    monkeypatch.setattr(settings, "vectorizer_primary_provider", "a8")
    # Instantiate AIClient
    # We need to mock the internal clients *after* instantiation or patch the classes *before* instantiation.
    # Since AIClient instantiates them in __init__, patching the classes is better.

    with patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        
        # Setup mocks
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value
        
        # A8 fails
        mock_a8_instance.image_to_vector = AsyncMock(side_effect=Exception("A8 Service Down"))
        
        # WebAPI succeeds
        expected_url = "http://example.com/result.svg"
        mock_webapi_instance.convert_image = AsyncMock(return_value=expected_url)
        
        # Initialize AIClient
        client = AIClient()
        
        # Call the method
        image_bytes = b"fake_image_bytes"
        result = await client.vectorize_image_webapi(image_bytes, options={"vectorFormat": ".svg"})
        
        # Verify results
        assert result == expected_url
        
        # Verify A8 was called
        mock_a8_instance.image_to_vector.assert_called_once()
        
        # Verify WebAPI was called (fallback happened)
        mock_webapi_instance.convert_image.assert_called_once()

@pytest.mark.asyncio
async def test_vectorize_image_webapi_a8_success(monkeypatch):
    monkeypatch.setattr(settings, "vectorizer_primary_provider", "a8")
    with patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        
        # Setup mocks
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value
        
        # A8 succeeds
        expected_url = "http://example.com/a8_result.svg"
        mock_a8_instance.image_to_vector = AsyncMock(return_value=expected_url)
        
        # Initialize AIClient
        client = AIClient()
        
        # Call the method
        image_bytes = b"fake_image_bytes"
        result = await client.vectorize_image_webapi(image_bytes, options={"vectorFormat": ".svg"})
        
        # Verify results
        assert result == expected_url
        
        # Verify A8 was called
        mock_a8_instance.image_to_vector.assert_called_once()
        
        # Verify WebAPI was NOT called
        mock_webapi_instance.convert_image.assert_not_called()


@pytest.mark.asyncio
async def test_vectorize_image_webapi_zfy_success(monkeypatch):
    monkeypatch.setattr(settings, "vectorizer_primary_provider", "zfy")

    with patch('app.services.ai_client.ai_client.ZfyVectorizerClient') as MockZfy, \
         patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        mock_zfy_instance = MockZfy.return_value
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value

        expected_url = "/files/results/vectorized_1234.eps"
        mock_zfy_instance.image_to_vector = AsyncMock(return_value=expected_url)

        client = AIClient()

        result = await client.vectorize_image_webapi(
            b"fake_image_bytes",
            options={"vectorFormat": ".eps", "original_filename": "sample.png"},
        )

        assert result == expected_url
        mock_zfy_instance.image_to_vector.assert_called_once_with(
            b"fake_image_bytes",
            fmt="eps",
            filename="sample.png",
        )
        mock_a8_instance.image_to_vector.assert_not_called()
        mock_webapi_instance.convert_image.assert_not_called()


@pytest.mark.asyncio
async def test_vectorize_image_webapi_zfy_uses_default_eps(monkeypatch):
    monkeypatch.setattr(settings, "vectorizer_primary_provider", "zfy")
    monkeypatch.setattr(settings, "vectorizer_default_format", ".eps")

    with patch('app.services.ai_client.ai_client.ZfyVectorizerClient') as MockZfy:
        mock_zfy_instance = MockZfy.return_value
        expected_url = "/files/results/vectorized_default.eps"
        mock_zfy_instance.image_to_vector = AsyncMock(return_value=expected_url)

        client = AIClient()

        result = await client.vectorize_image_webapi(b"fake_image_bytes")

        assert result == expected_url
        mock_zfy_instance.image_to_vector.assert_called_once_with(
            b"fake_image_bytes",
            fmt="eps",
            filename=None,
        )


@pytest.mark.asyncio
async def test_vectorizer_client_delegates_to_new_protocol():
    zfy_client = MagicMock()
    zfy_client.base_url = "https://a8.zifeiyuai.top:2345"
    zfy_client.image_to_vector = AsyncMock(return_value="/files/results/vectorized.svg")

    client = VectorizerClient(zfy_client=zfy_client)
    result = await client.vectorize_image(
        b"fake_image_bytes",
        options={"vectorFormat": ".svg", "original_filename": "sample.png"},
    )

    assert result == "/files/results/vectorized.svg"
    assert client.vectorizer_url == "https://a8.zifeiyuai.top:2345/add_task"
    zfy_client.image_to_vector.assert_awaited_once_with(
        b"fake_image_bytes",
        fmt="svg",
        filename="sample.png",
    )


@pytest.mark.asyncio
async def test_vectorize_image_webapi_zfy_falls_back_to_legacy(monkeypatch):
    monkeypatch.setattr(settings, "vectorizer_primary_provider", "zfy")
    monkeypatch.setattr(settings, "vectorizer_fallback_to_legacy", True)

    with patch('app.services.ai_client.ai_client.ZfyVectorizerClient') as MockZfy, \
         patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        mock_zfy_instance = MockZfy.return_value
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value

        mock_zfy_instance.image_to_vector = AsyncMock(side_effect=Exception("ZFY down"))
        expected_url = "/files/results/vectorized_legacy.svg"
        mock_a8_instance.image_to_vector = AsyncMock(return_value=expected_url)

        client = AIClient()

        result = await client.vectorize_image_webapi(
            b"fake_image_bytes",
            options={"vectorFormat": ".svg"},
        )

        assert result == expected_url
        mock_zfy_instance.image_to_vector.assert_called_once()
        mock_a8_instance.image_to_vector.assert_called_once()
        mock_webapi_instance.convert_image.assert_not_called()


@pytest.mark.asyncio
async def test_vectorize_image_webapi_zfy_does_not_fallback_by_default(monkeypatch):
    monkeypatch.setattr(settings, "vectorizer_primary_provider", "zfy")
    monkeypatch.setattr(settings, "vectorizer_fallback_to_legacy", False)

    with patch('app.services.ai_client.ai_client.ZfyVectorizerClient') as MockZfy, \
         patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        mock_zfy_instance = MockZfy.return_value
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value

        mock_zfy_instance.image_to_vector = AsyncMock(side_effect=Exception("ZFY down"))

        client = AIClient()

        with pytest.raises(Exception, match="ZFY down"):
            await client.vectorize_image_webapi(
                b"fake_image_bytes",
                options={"vectorFormat": ".eps"},
            )

        mock_zfy_instance.image_to_vector.assert_called_once()
        mock_a8_instance.image_to_vector.assert_not_called()
        mock_webapi_instance.convert_image.assert_not_called()


@pytest.mark.asyncio
async def test_save_generated_eps_result(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "upload_path", str(tmp_path))

    service = FileService()
    monkeypatch.setattr(service, "should_use_oss", lambda: False)

    result_url = await service.save_upload_file(
        b"%!PS-Adobe-3.0 EPSF-3.0\n",
        "vectorized_test.eps",
        subfolder="results",
        validate_dimensions=False,
        validate_file_size=False,
    )

    assert result_url.startswith("/files/results/")
    assert result_url.endswith(".eps")


def test_zfy_detects_eps_response():
    assert (
        ZfyVectorizerClient._detect_result_format(
            b"%!PS-Adobe-3.0 EPSF-3.0\n",
            requested_fmt="svg",
            headers={},
        )
        == "eps"
    )


@pytest.mark.asyncio
async def test_a8_sends_zfy_api_key_header(monkeypatch):
    requests = []

    class FakeAsyncClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, **kwargs):
            requests.append(("post", url, kwargs))
            return httpx.Response(200, json={"code": 0, "id": "task-123"})

        async def get(self, url, **kwargs):
            requests.append(("get", url, kwargs))
            if url.endswith("/try_get"):
                return httpx.Response(200, json={"code": 0})
            return httpx.Response(
                200,
                content=b"%!PS-Adobe-3.0 EPSF-3.0\n",
                headers={"content-type": "application/postscript"},
            )

    monkeypatch.setattr(
        "app.services.ai_client.a8_vectorizer_client.httpx.AsyncClient",
        FakeAsyncClient,
    )
    monkeypatch.setattr(
        "app.services.ai_client.a8_vectorizer_client.api_limiter.slot",
        noop_api_slot,
    )

    client = A8VectorizerClient(
        base_url="https://a8.zifeiyuai.top:2345",
        api_key="test-key",
    )
    client.file_service.save_upload_file = AsyncMock(
        return_value="/files/results/vectorized.eps"
    )

    result = await client.image_to_vector(b"fake_image_bytes", fmt="eps")

    assert result == "/files/results/vectorized.eps"
    assert [call[0] for call in requests] == ["post", "get", "get"]
    assert all(
        call_kwargs["headers"] == {"zfyai-api-key": "test-key"}
        for _, _, call_kwargs in requests
    )
    client.file_service.save_upload_file.assert_awaited_once()
    _, save_args, save_kwargs = client.file_service.save_upload_file.mock_calls[0]
    assert save_args[1].endswith(".eps")
    assert save_kwargs["validate_dimensions"] is False
    assert save_kwargs["validate_file_size"] is False


@pytest.mark.asyncio
async def test_zfy_retries_transient_request_errors(monkeypatch):
    calls = 0
    response = httpx.Response(200, json={"code": 0})

    class FakeAsyncClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                request = httpx.Request("GET", url)
                raise httpx.ConnectError("temporary connect failure", request=request)
            return response

    monkeypatch.setattr(
        "app.services.ai_client.zfy_vectorizer_client.httpx.AsyncClient",
        FakeAsyncClient,
    )
    monkeypatch.setattr(
        "app.services.ai_client.zfy_vectorizer_client.api_limiter.slot",
        noop_api_slot,
    )
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.ai_client.zfy_vectorizer_client.asyncio.sleep", sleep)

    client = ZfyVectorizerClient(api_key="test-key")
    result = await client._request_with_retries(
        "get",
        "https://example.com/try_get",
        purpose="try_get",
        attempts=2,
    )

    assert result is response
    assert calls == 2
    sleep.assert_awaited_once_with(1)
