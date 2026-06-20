import asyncio
import time
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.ai_client.ai_client import AIClient


def _build_client() -> AIClient:
    client = AIClient.__new__(AIClient)
    client.image_utils = SimpleNamespace(
        _build_pattern_prompt=lambda pattern_type: f"prompt:{pattern_type}",
        extract_pattern=None,
        apyi_gemini_client=SimpleNamespace(
            generate_image_preview=None,
            _extract_image_url=lambda _result: None,
        ),
    )
    client.apyi_gemini_client = SimpleNamespace(
        generate_image_preview=None,
        _extract_image_url=lambda _result: None,
    )
    client.tuzi_gemini_client = SimpleNamespace(
        generate_image_preview=None,
        _extract_image_url=lambda _result: None,
    )
    client.tuzi_openai_client = SimpleNamespace(edit_image=None, extract_image_url=None)
    client.haoee_gemini_client = SimpleNamespace(
        generate_image_preview=None,
        _extract_image_url=lambda _result: None,
    )
    client.runninghub_client = SimpleNamespace(run_workflow_with_custom_nodes=None)
    return client


@pytest.mark.asyncio
async def test_extract_pattern_combined_returns_early_when_enough_results(monkeypatch):
    client = _build_client()
    cancelled = {"tuzi": False, "runninghub": False}

    async def fake_extract_pattern(_image_bytes, options):
        pattern_type = options["pattern_type"]
        if pattern_type == "combined_detail":
            await asyncio.sleep(0.02)
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {pattern_type}")

    async def fake_apyi_generate_image_preview(*_args, **_kwargs):
        await asyncio.sleep(0.01)
        return {"candidates": [{"content": {"parts": [{"text": "https://example.com/general.png"}]}}]}

    async def slow_edit_image(**_kwargs):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled["tuzi"] = True
            raise

    async def slow_runninghub(**_kwargs):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled["runninghub"] = True
            raise

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 180)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 2)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "generate_image_preview",
        fake_apyi_generate_image_preview,
    )
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/general.png",
    )
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", slow_edit_image)
    monkeypatch.setattr(client.tuzi_openai_client, "extract_image_url", lambda _result: None)

    result = await client._extract_pattern_combined(
        b"fake-image",
        {"original_image_url": "https://example.com/source.png", "aspect_ratio": "1:1"},
    )

    assert result == "https://example.com/general.png,https://example.com/detail.png"
    assert cancelled == {"tuzi": True, "runninghub": True}


@pytest.mark.asyncio
async def test_extract_pattern_combined_allows_timeouts_when_other_branches_succeed(monkeypatch):
    client = _build_client()

    async def fake_extract_pattern(_image_bytes, options):
        pattern_type = options["pattern_type"]
        if pattern_type == "combined_detail":
            await asyncio.sleep(1)
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {pattern_type}")

    async def fake_apyi_generate_image_preview(*_args, **_kwargs):
        return {"candidates": [{"content": {"parts": [{"text": "https://example.com/general.png"}]}}]}

    async def fast_edit_image(**_kwargs):
        return {"data": [{"url": "https://example.com/gpt2.png"}]}

    async def slow_runninghub(**_kwargs):
        await asyncio.sleep(1)
        return ["https://example.com/runninghub.png"]

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.05)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 4)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "generate_image_preview",
        fake_apyi_generate_image_preview,
    )
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/general.png",
    )
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", fast_edit_image)
    monkeypatch.setattr(
        client.tuzi_openai_client,
        "extract_image_url",
        lambda result: result["data"][0]["url"],
    )

    started = time.monotonic()
    result = await client._extract_pattern_combined(
        b"fake-image",
        {"original_image_url": "https://example.com/source.png", "aspect_ratio": "1:1"},
    )
    elapsed = time.monotonic() - started

    assert set(result.split(",")) == {
        "https://example.com/general.png",
        "https://example.com/gpt2.png",
    }
    assert elapsed < 0.3


@pytest.mark.asyncio
async def test_extract_pattern_combined_routes_general_2_to_apyi_by_default(monkeypatch):
    client = _build_client()
    captured = {}

    async def fake_extract_pattern(_image_bytes, options):
        if options["pattern_type"] == "combined_detail":
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {options['pattern_type']}")

    async def fake_apyi_generate_image_preview(image_bytes, prompt, mime_type, **kwargs):
        captured["image_bytes"] = image_bytes
        captured["prompt"] = prompt
        captured["mime_type"] = mime_type
        captured["kwargs"] = kwargs
        return {"ok": True}

    async def slow_edit_image(**_kwargs):
        await asyncio.sleep(10)

    async def slow_runninghub(**_kwargs):
        await asyncio.sleep(10)

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.02)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 2)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "generate_image_preview",
        fake_apyi_generate_image_preview,
    )
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/general.png",
    )
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", slow_edit_image)
    monkeypatch.setattr(client.tuzi_openai_client, "extract_image_url", lambda _result: None)

    result = await client._extract_pattern_combined(
        b"fake-image",
        {"original_image_url": "https://example.com/source.png", "aspect_ratio": "1:1"},
    )

    assert set(result.split(",")) == {
        "https://example.com/general.png",
        "https://example.com/detail.png",
    }
    assert captured["image_bytes"] == b"fake-image"
    assert captured["prompt"] == "prompt:general_2"
    assert captured["mime_type"] == "image/png"
    assert captured["kwargs"] == {
        "aspect_ratio": "1:1",
        "resolution": "4K",
        "model_name": "gemini-3-pro-image-preview-4k",
    }


@pytest.mark.asyncio
async def test_extract_pattern_combined_routes_general_2_to_tuzi_from_snapshot(monkeypatch):
    client = _build_client()
    called = {"apyi": False, "tuzi": False}
    captured = {}

    async def fake_extract_pattern(_image_bytes, options):
        if options["pattern_type"] == "combined_detail":
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {options['pattern_type']}")

    async def fake_apyi_generate_image_preview(*_args, **_kwargs):
        called["apyi"] = True
        return {"ok": True}

    async def fake_tuzi_generate_image_preview(image_bytes, prompt, mime_type, **kwargs):
        called["tuzi"] = True
        captured["image_bytes"] = image_bytes
        captured["prompt"] = prompt
        captured["mime_type"] = mime_type
        captured["kwargs"] = kwargs
        return {"ok": True}

    async def slow_edit_image(**_kwargs):
        await asyncio.sleep(10)

    async def slow_runninghub(**_kwargs):
        await asyncio.sleep(10)

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.02)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 2)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "generate_image_preview",
        fake_apyi_generate_image_preview,
    )
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/apyi.png",
    )
    monkeypatch.setattr(
        client.tuzi_gemini_client,
        "generate_image_preview",
        fake_tuzi_generate_image_preview,
    )
    monkeypatch.setattr(
        client.tuzi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/tuzi.png",
    )
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", slow_edit_image)
    monkeypatch.setattr(client.tuzi_openai_client, "extract_image_url", lambda _result: None)

    result = await client._extract_pattern_combined(
        b"fake-image",
        {
            "original_image_url": "https://example.com/source.png",
            "aspect_ratio": "1:1",
            "ai_model_routes": {
                "extract_pattern.combined.general_2": {
                    "provider": "tuzi",
                    "model": "gemini-3.1-flash-image-preview-2k",
                }
            },
        },
    )

    assert set(result.split(",")) == {
        "https://example.com/tuzi.png",
        "https://example.com/detail.png",
    }
    assert called == {"apyi": False, "tuzi": True}
    assert captured["image_bytes"] == b"fake-image"
    assert captured["prompt"] == "prompt:general_2"
    assert captured["mime_type"] == "image/png"
    assert captured["kwargs"] == {
        "aspect_ratio": "1:1",
        "resolution": "2K",
        "model_name": "gemini-3.1-flash-image-preview",
    }


@pytest.mark.asyncio
async def test_extract_pattern_combined_routes_general_2_to_haoee_from_snapshot(monkeypatch):
    client = _build_client()
    called = {"apyi": False, "haoee": False}
    captured = {}

    async def fake_extract_pattern(_image_bytes, options):
        if options["pattern_type"] == "combined_detail":
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {options['pattern_type']}")

    async def fake_apyi_generate_image_preview(*_args, **_kwargs):
        called["apyi"] = True
        return {"ok": True}

    async def fake_haoee_generate_image_preview(image_bytes, prompt, mime_type, **kwargs):
        called["haoee"] = True
        captured["image_bytes"] = image_bytes
        captured["prompt"] = prompt
        captured["mime_type"] = mime_type
        captured["kwargs"] = kwargs
        return {"ok": True}

    async def slow_edit_image(**_kwargs):
        await asyncio.sleep(10)

    async def slow_runninghub(**_kwargs):
        await asyncio.sleep(10)

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.02)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 2)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "generate_image_preview",
        fake_apyi_generate_image_preview,
    )
    monkeypatch.setattr(
        client.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/apyi.png",
    )
    monkeypatch.setattr(
        client.haoee_gemini_client,
        "generate_image_preview",
        fake_haoee_generate_image_preview,
    )
    monkeypatch.setattr(
        client.haoee_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/haoee.png",
    )
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", slow_edit_image)
    monkeypatch.setattr(client.tuzi_openai_client, "extract_image_url", lambda _result: None)

    result = await client._extract_pattern_combined(
        b"fake-image",
        {
            "original_image_url": "https://example.com/source.png",
            "aspect_ratio": "1:1",
            "ai_model_routes": {
                "extract_pattern.combined.general_2": {
                    "provider": "haoee",
                    "model": "gemini-3-pro-image-preview-4k",
                }
            },
        },
    )

    assert set(result.split(",")) == {
        "https://example.com/haoee.png",
        "https://example.com/detail.png",
    }
    assert called == {"apyi": False, "haoee": True}
    assert captured["image_bytes"] == b"fake-image"
    assert captured["prompt"] == "prompt:general_2"
    assert captured["mime_type"] == "image/png"
    assert captured["kwargs"] == {
        "aspect_ratio": "1:1",
        "resolution": "4K",
        "model_name": "gemini-3-pro-image-preview-lite",
    }


@pytest.mark.asyncio
async def test_extract_pattern_combined_t2_runs_three_2k_and_one_gpt2(monkeypatch):
    client = _build_client()
    haoee_captured = []
    tuzi_captured = []

    async def fake_haoee_generate_image_preview(image_bytes, prompt, mime_type, **kwargs):
        index = len(haoee_captured) + 1
        haoee_captured.append(
            {
                "image_bytes": image_bytes,
                "prompt": prompt,
                "mime_type": mime_type,
                "kwargs": kwargs,
            }
        )
        return {"url": f"https://example.com/banana-{index}.png"}

    async def fake_tuzi_edit_image(**kwargs):
        tuzi_captured.append(kwargs)
        return {"data": [{"url": "https://example.com/gpt2.png"}]}

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 1)
    monkeypatch.setattr(
        settings,
        "haoee_maas_default_preview_model",
        "gemini-3-pro-image-preview-lite",
    )
    monkeypatch.setattr(
        client.haoee_gemini_client,
        "generate_image_preview",
        fake_haoee_generate_image_preview,
    )
    monkeypatch.setattr(
        client.haoee_gemini_client,
        "_extract_image_url",
        lambda result: result["url"],
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", fake_tuzi_edit_image)
    monkeypatch.setattr(
        client.tuzi_openai_client,
        "extract_image_url",
        lambda result: result["data"][0]["url"],
    )

    result = await client._extract_pattern_combined_t2(
        b"fake-image",
        {"aspect_ratio": "1:1"},
    )

    assert result.split(",") == [
        "https://example.com/banana-1.png",
        "https://example.com/banana-2.png",
        "https://example.com/banana-3.png",
        "https://example.com/gpt2.png",
    ]
    assert [item["kwargs"]["resolution"] for item in haoee_captured] == [
        "2K",
        "2K",
        "2K",
    ]
    assert all(item["image_bytes"] == b"fake-image" for item in haoee_captured)
    assert all(item["prompt"] == "prompt:general_2" for item in haoee_captured)
    assert all(item["mime_type"] == "image/png" for item in haoee_captured)
    assert all(item["kwargs"]["aspect_ratio"] == "1:1" for item in haoee_captured)
    assert all(
        item["kwargs"]["model_name"] == "gemini-3-pro-image-preview-lite"
        for item in haoee_captured
    )
    assert tuzi_captured == [
        {
            "image_bytes": b"fake-image",
            "prompt": (
                "提取图中衣服上的图案，去掉褶皱、阴影，图案细节必须跟原图一模一样。"
                "输出4K高清平面印刷图案，只保留图案本身和干净底色，不要生成衣服形状。"
            ),
            "mime_type": "image/png",
            "model": "gpt-image-2-vip",
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("num_images", "expected_urls", "expected_haoee_resolutions", "expected_tuzi_calls"),
    [
        (1, ["https://example.com/banana-1.png"], ["2K"], 0),
        (
            2,
            ["https://example.com/banana-1.png", "https://example.com/gpt2.png"],
            ["2K"],
            1,
        ),
        (
            4,
            [
                "https://example.com/banana-1.png",
                "https://example.com/banana-2.png",
                "https://example.com/banana-3.png",
                "https://example.com/gpt2.png",
            ],
            ["2K", "2K", "2K"],
            1,
        ),
    ],
)
async def test_extract_pattern_combined_t2_respects_num_images(
    monkeypatch,
    num_images,
    expected_urls,
    expected_haoee_resolutions,
    expected_tuzi_calls,
):
    client = _build_client()
    haoee_captured = []
    tuzi_captured = []

    async def fake_haoee_generate_image_preview(image_bytes, prompt, mime_type, **kwargs):
        index = len(haoee_captured) + 1
        haoee_captured.append(kwargs)
        return {"url": f"https://example.com/banana-{index}.png"}

    async def fake_tuzi_edit_image(**kwargs):
        tuzi_captured.append(kwargs)
        return {"data": [{"url": "https://example.com/gpt2.png"}]}

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 1)
    monkeypatch.setattr(
        settings,
        "haoee_maas_default_preview_model",
        "gemini-3-pro-image-preview-lite",
    )
    monkeypatch.setattr(
        client.haoee_gemini_client,
        "generate_image_preview",
        fake_haoee_generate_image_preview,
    )
    monkeypatch.setattr(
        client.haoee_gemini_client,
        "_extract_image_url",
        lambda result: result["url"],
    )
    monkeypatch.setattr(client.tuzi_openai_client, "edit_image", fake_tuzi_edit_image)
    monkeypatch.setattr(
        client.tuzi_openai_client,
        "extract_image_url",
        lambda result: result["data"][0]["url"],
    )

    result = await client._extract_pattern_combined_t2(
        b"fake-image",
        {"aspect_ratio": "1:1", "num_images": num_images},
    )

    assert result.split(",") == expected_urls
    assert [item["resolution"] for item in haoee_captured] == expected_haoee_resolutions
    assert len(tuzi_captured) == expected_tuzi_calls


@pytest.mark.asyncio
async def test_extract_pattern_general_1_retries_missing_workflow_result(monkeypatch):
    client = _build_client()
    attempts = {"wf-1": 0, "wf-2": 0}

    async def fake_runninghub(**kwargs):
        workflow_id = kwargs["workflow_id"]
        attempts[workflow_id] += 1
        if workflow_id == "wf-1":
            if attempts[workflow_id] == 1:
                return []
            return ["https://example.com/one.png"]
        if workflow_id == "wf-2":
            return ["https://example.com/two.png"]
        raise AssertionError(f"unexpected workflow_id: {workflow_id}")

    monkeypatch.setattr(settings, "extract_pattern_general_workflow_attempts", 2)
    monkeypatch.setattr(settings, "runninghub_workflow_id_extract_general1_2img_1", "wf-1")
    monkeypatch.setattr(settings, "runninghub_workflow_id_extract_general1_2img_2", "wf-2")
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        fake_runninghub,
    )

    result = await client._extract_pattern_general_1(
        b"fake-image",
        {"num_images": 2},
    )

    assert result == "https://example.com/one.png,https://example.com/two.png"
    assert attempts == {"wf-1": 2, "wf-2": 1}


@pytest.mark.asyncio
async def test_extract_pattern_general_1_fails_when_requested_count_not_met(monkeypatch):
    client = _build_client()

    async def fake_runninghub(**kwargs):
        workflow_id = kwargs["workflow_id"]
        if workflow_id == "wf-1":
            return ["https://example.com/one.png"]
        return []

    monkeypatch.setattr(settings, "extract_pattern_general_workflow_attempts", 1)
    monkeypatch.setattr(settings, "runninghub_workflow_id_extract_general1_1", "wf-1")
    monkeypatch.setattr(settings, "runninghub_workflow_id_extract_general1_2", "wf-2")
    monkeypatch.setattr(settings, "runninghub_workflow_id_extract_general1_3", "wf-3")
    monkeypatch.setattr(settings, "runninghub_workflow_id_extract_general1_4", "wf-4")
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        fake_runninghub,
    )

    with pytest.raises(Exception, match="仅获得1/4张结果"):
        await client._extract_pattern_general_1(
            b"fake-image",
            {"num_images": 4},
        )
