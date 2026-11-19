from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.core.config import settings
from app.services.ai_client.ai_client import AIClient
from app.services.ai_client.gemini_routes import generate_routed_image
from app.services.ai_client.image_utils import ImageProcessingUtils
from app.services.ai_model_route_service import (
    AI_MODEL_ROUTES_OPTION_KEY,
    SUPPORTED_AI_MODEL_ROUTES,
    AIModelRouteConfigError,
    AIModelRouteService,
)
from app.services.ai_route_catalog import (
    DENOISE_ROUTE,
    FLAT_TO_3D_ROUTE,
    GENERAL2_ROUTE,
    PROMPT_EDIT_2K_ROUTE,
    PROMPT_EDIT_4K_ROUTE,
    PROMPT_EDIT_PRO_ROUTE,
    SEAMLESS_ROUTE,
    UPSCALE_ROUTE,
    VECTOR_ROUTE,
    YARN_ROUTE,
)


@pytest.fixture
def configured(monkeypatch):
    for key in (
        "apiyi_api_key",
        "tuzi_api_key",
        "haoee_maas_api_key",
        "krapi_api_key",
        "meitu_api_key",
        "meitu_api_secret",
        "runninghub_api_key",
        "vector_zfy_api_key",
        "vector_webapi_key",
        "seedream_api_key",
    ):
        monkeypatch.setattr(settings, key, "offline-key")


def options(key, provider="krapi", route_model=None, **extra):
    if route_model is None:
        route_model = SUPPORTED_AI_MODEL_ROUTES[key]["providers"][provider][
            "default_model"
        ]
    return {
        AI_MODEL_ROUTES_OPTION_KEY: {key: {"provider": provider, "model": route_model}},
        **extra,
    }


@pytest.mark.parametrize(
    "task_type,extra,key",
    [
        ("prompt_edit", {"model": "new"}, PROMPT_EDIT_2K_ROUTE),
        ("prompt_edit", {"model": "original"}, PROMPT_EDIT_2K_ROUTE),
        ("prompt_edit", {"model": "pro_4k"}, PROMPT_EDIT_4K_ROUTE),
        ("prompt_edit", {"model": "seedream_pro"}, PROMPT_EDIT_PRO_ROUTE),
        ("denoise", {}, DENOISE_ROUTE),
        ("flat_to_3d", {}, FLAT_TO_3D_ROUTE),
        ("embroidery", {"embroidery_mode": "yarn"}, YARN_ROUTE),
        ("seamless", {}, SEAMLESS_ROUTE),
        ("vectorize", {}, VECTOR_ROUTE),
        ("upscale", {"engine": "runninghub_vr2"}, UPSCALE_ROUTE),
    ],
)
def test_snapshot_frozen_when_admin_changes_route(
    db_session, configured, task_type, extra, key
):
    service = AIModelRouteService()
    provider = (
        "webapi"
        if key == VECTOR_ROUTE
        else "meitu_v2"
        if key == UPSCALE_ROUTE
        else "krapi"
    )
    service.update_routes(db_session, [{"routeKey": key, "provider": provider}])
    frozen = service.apply_route_snapshot(db_session, task_type, extra, overwrite=True)
    before = deepcopy(frozen)
    default = service._default_selection(key)
    service.update_routes(db_session, [{"routeKey": key, **default}])
    assert (
        service.apply_route_snapshot(db_session, task_type, frozen, overwrite=False)
        == before
    )
    assert frozen[AI_MODEL_ROUTES_OPTION_KEY][key]["provider"] == provider
    assert frozen.get("model") == extra.get("model")
    assert frozen.get("engine") == extra.get("engine")


def test_legacy_task_does_not_adopt_new_admin_selection(db_session, configured):
    service = AIModelRouteService()
    service.update_routes(
        db_session, [{"routeKey": PROMPT_EDIT_4K_ROUTE, "provider": "krapi"}]
    )
    old = service.apply_route_snapshot(
        db_session, "prompt_edit", {"model": "pro_4k"}, overwrite=False
    )
    new = service.apply_route_snapshot(
        db_session, "prompt_edit", {"model": "pro_4k"}, overwrite=True
    )
    assert old[AI_MODEL_ROUTES_OPTION_KEY][PROMPT_EDIT_4K_ROUTE]["provider"] == "apyi"
    assert new[AI_MODEL_ROUTES_OPTION_KEY][PROMPT_EDIT_4K_ROUTE]["provider"] == "krapi"


def test_single_routes_read_only_and_missing_credentials_rejected(
    db_session, monkeypatch
):
    service = AIModelRouteService()
    monkeypatch.setattr(settings, "krapi_api_key", "")
    with pytest.raises(AIModelRouteConfigError, match="凭据"):
        service.update_routes(
            db_session, [{"routeKey": PROMPT_EDIT_4K_ROUTE, "provider": "krapi"}]
        )
    with pytest.raises(AIModelRouteConfigError, match="单线路"):
        service.update_routes(
            db_session, [{"routeKey": "expand_image", "provider": "runninghub"}]
        )
    routes = service.get_admin_routes(db_session)["routes"]
    route = next(r for r in routes if r["routeKey"] == PROMPT_EDIT_4K_ROUTE)
    kr = next(p for p in route["providers"] if p["provider"] == "krapi")
    assert kr["configured"] is False
    assert "api_key" not in str(routes)
    assert all(
        r["readOnly"]
        for r in routes
        if r["routeKey"] in {"expand_image", "seamless_loop", "upscale.4k"}
    )


@pytest.mark.parametrize("key", [PROMPT_EDIT_4K_ROUTE, DENOISE_ROUTE])
def test_4k_routes_reject_2k_models_and_seedream(db_session, configured, key):
    service = AIModelRouteService()
    for selection in [
        {"provider": "apyi", "model": "gemini-3.1-flash-image-preview-2k"},
        {"provider": "seedream", "model": "seedream"},
    ]:
        with pytest.raises(AIModelRouteConfigError):
            service.update_routes(db_session, [{"routeKey": key, **selection}])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,key",
    [
        ("new", PROMPT_EDIT_2K_ROUTE),
        ("original", PROMPT_EDIT_2K_ROUTE),
        ("pro_4k", PROMPT_EDIT_4K_ROUTE),
    ],
)
@pytest.mark.parametrize("reference", [False, True])
async def test_prompt_edit_dispatches_selected_provider_with_reference(
    mode, key, reference
):
    utils = ImageProcessingUtils.__new__(ImageProcessingUtils)
    selected = SimpleNamespace(
        generate_image_preview=AsyncMock(return_value={}),
        generate_image_preview_multi=AsyncMock(return_value={}),
        _extract_image_url=lambda response: "/files/selected.png",
        SUPPORTED_ASPECT_RATIOS=["1:1"],
    )
    utils.krapi_gemini_client = selected
    utils.apyi_gemini_client = SimpleNamespace(
        generate_image_preview_multi=AsyncMock(
            side_effect=AssertionError("No fallback")
        )
    )
    opts = options(
        key,
        route_model="T香蕉2-4K" if mode == "pro_4k" else "T香蕉2",
        model_choice=mode,
        instruction="only change background",
    )
    opts["model"] = mode
    if reference:
        opts["secondary_image_bytes"] = b"reference"
    assert await utils.prompt_edit_image(b"primary", opts) == "/files/selected.png"
    call = (
        selected.generate_image_preview_multi
        if reference
        else selected.generate_image_preview
    )
    assert call.await_count == 1
    assert call.await_args.kwargs["resolution"] == ("4K" if mode == "pro_4k" else "2K")
    if reference:
        assert call.await_args.args[0] == [b"primary", b"reference"]
    utils.apyi_gemini_client.generate_image_preview_multi.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["tuzi", "haoee"])
async def test_secondary_images_kept_in_tuzi_haoee_protocol(provider):
    selected = SimpleNamespace(
        _image_to_base64=lambda raw, fmt: raw.decode(),
        _make_request=AsyncMock(return_value={}),
        _extract_image_url=lambda response: "/files/multi.png",
        SUPPORTED_ASPECT_RATIOS=["1:1"],
        _ensure_credentials=lambda: None,
        _resolve_endpoint_model=lambda model: model,
    )
    owner = SimpleNamespace(
        **{
            (
                "tuzi_gemini_client" if provider == "tuzi" else "haoee_gemini_client"
            ): selected
        }
    )
    assert (
        await generate_routed_image(
            owner,
            [b"first", b"second"],
            "edit",
            options(PROMPT_EDIT_4K_ROUTE, provider),
            "prompt_edit.model1.4k",
        )
        == "/files/multi.png"
    )
    payload = selected._make_request.await_args.args[2]
    assert [p["inline_data"]["data"] for p in payload["contents"][0]["parts"][1:]] == [
        "first",
        "second",
    ]
    assert payload["generationConfig"]["imageConfig"]["imageSize"] == "4K"


@pytest.mark.asyncio
async def test_selected_provider_failure_does_not_call_another_provider():
    chosen = SimpleNamespace(
        generate_image_preview=AsyncMock(side_effect=RuntimeError("429")),
        SUPPORTED_ASPECT_RATIOS=["1:1"],
    )
    owner = SimpleNamespace(
        krapi_gemini_client=chosen,
        apyi_gemini_client=SimpleNamespace(generate_image_preview=AsyncMock()),
    )
    with pytest.raises(RuntimeError, match="429"):
        await generate_routed_image(
            owner, [b"image"], "edit", options(DENOISE_ROUTE), DENOISE_ROUTE
        )
    chosen.generate_image_preview.assert_awaited_once()
    owner.apyi_gemini_client.generate_image_preview.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,key,extra",
    [
        ("denoise_image", DENOISE_ROUTE, {}),
        ("seamless_pattern_conversion", SEAMLESS_ROUTE, {}),
        ("extract_pattern", GENERAL2_ROUTE, {"pattern_type": "general_2"}),
    ],
)
async def test_image_utils_other_functions_use_manual_route(method, key, extra):
    utils = ImageProcessingUtils.__new__(ImageProcessingUtils)
    utils.krapi_gemini_client = SimpleNamespace(
        generate_image_preview=AsyncMock(return_value={}),
        _extract_image_url=lambda response: "/files/result.png",
        SUPPORTED_ASPECT_RATIOS=["1:1"],
    )
    result = await getattr(utils, method)(b"image", options(key, **extra))
    assert result == "/files/result.png"
    utils.krapi_gemini_client.generate_image_preview.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,key,extra",
    [
        ("convert_flat_to_3d", FLAT_TO_3D_ROUTE, {}),
        ("enhance_embroidery", YARN_ROUTE, {"embroidery_mode": "yarn"}),
        (
            "prompt_edit_image",
            PROMPT_EDIT_PRO_ROUTE,
            {"model": "seedream_pro", "instruction": "keep shape"},
        ),
    ],
)
async def test_ai_client_direct_features_use_manual_route(method, key, extra):
    ai = AIClient.__new__(AIClient)
    ai.krapi_gemini_client = SimpleNamespace(
        generate_image_preview=AsyncMock(return_value={}),
        _extract_image_url=lambda response: "/files/result.png",
        SUPPORTED_ASPECT_RATIOS=["1:1"],
    )
    ai.seedream_client = SimpleNamespace(
        generate=AsyncMock(side_effect=AssertionError("No automatic fallback"))
    )
    assert (
        await getattr(ai, method)(b"image", options(key, **extra))
        == "/files/result.png"
    )
    ai.seedream_client.generate.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["zfy", "a8", "webapi"])
async def test_manual_vector_route_does_not_fallback(provider):
    ai = AIClient.__new__(AIClient)
    ai.zfy_vectorizer_client = SimpleNamespace(
        image_to_vector=AsyncMock(return_value="vector.eps")
    )
    ai.a8_vectorizer_client = SimpleNamespace(
        image_to_vector=AsyncMock(return_value="vector.eps")
    )
    ai.vector_webapi_client = SimpleNamespace(
        convert_image=AsyncMock(return_value="vector.eps")
    )
    assert (
        await ai.vectorize_image_webapi(b"image", options(VECTOR_ROUTE, provider))
        == "vector.eps"
    )
    methods = {
        "zfy": ai.zfy_vectorizer_client.image_to_vector,
        "a8": ai.a8_vectorizer_client.image_to_vector,
        "webapi": ai.vector_webapi_client.convert_image,
    }
    assert sum(m.await_count for m in methods.values()) == 1
    methods[provider].side_effect = RuntimeError("unavailable")
    with pytest.raises(RuntimeError):
        await ai.vectorize_image_webapi(b"image", options(VECTOR_ROUTE, provider))
    assert all(m.await_count == 0 for p, m in methods.items() if p != provider)


@pytest.mark.asyncio
async def test_upscale_route_preserves_billing_engine_and_4k_boundary():
    ai = AIClient.__new__(AIClient)
    ai._prepare_image_for_external_api = AsyncMock(
        return_value=("https://example/input.png", b"image")
    )
    ai._upscale_with_meitu_v2 = AsyncMock(return_value="output.png")
    ai._upscale_with_4k_ultra = AsyncMock(return_value="ultra.png")
    opts = options(UPSCALE_ROUTE, "meitu_v2", engine="runninghub_vr2")
    assert (
        await ai.upscale_image("https://example/input.png", options=opts)
        == "output.png"
    )
    assert opts["engine"] == "runninghub_vr2"
    assert (
        await ai.upscale_image(
            "https://example/input.png",
            options={**opts, "engine": "runninghub_4k_ultra"},
        )
        == "ultra.png"
    )
    ai._upscale_with_meitu_v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_native_seamless_default_retains_original_gemini25_call():
    chosen = SimpleNamespace(
        process_image=AsyncMock(return_value={}),
        generate_image_preview=AsyncMock(),
        _extract_image_url=lambda response: "/files/native.png",
        SUPPORTED_ASPECT_RATIOS=["1:1"],
    )
    assert (
        await generate_routed_image(
            SimpleNamespace(apyi_gemini_client=chosen),
            [b"image"],
            "original prompt",
            options(SEAMLESS_ROUTE, "apyi"),
            SEAMLESS_ROUTE,
        )
        == "/files/native.png"
    )
    chosen.process_image.assert_awaited_once()
    chosen.generate_image_preview.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_children_and_reference_keep_creation_time_route(
    db_session, configured, monkeypatch
):
    from decimal import Decimal
    from unittest.mock import patch

    from app.models.task import Task
    from app.models.user import User
    from app.services.batch_processing_service import BatchProcessingService

    service = BatchProcessingService()
    routes = AIModelRouteService()
    routes.update_routes(
        db_session,
        [{"routeKey": PROMPT_EDIT_4K_ROUTE, "provider": "krapi", "model": "T香蕉pro"}],
    )
    user = User(
        user_id="batch-route-test",
        phone="qa-batch-route",
        hashed_password="unused",
        credits=100,
    )
    db_session.add(user)
    db_session.commit()
    monkeypatch.setattr(
        service.file_service,
        "prepare_upload_image",
        lambda raw, name: (raw, name, {"width": 512, "height": 512}, {}),
    )
    monkeypatch.setattr(
        service.file_service,
        "save_upload_file",
        AsyncMock(return_value="/files/shared.png"),
    )
    monkeypatch.setattr(
        service.membership_service,
        "calculate_service_cost",
        AsyncMock(return_value=Decimal("1.50")),
    )

    def dont_schedule(coro):
        coro.close()

    with patch(
        "app.services.batch_processing_service.asyncio.create_task",
        side_effect=dont_schedule,
    ):
        batch = await service.create_batch_task(
            db_session,
            user,
            "prompt_edit",
            [(b"one", "one.png"), (b"two", "two.png")],
            options={"model": "pro_4k", "instruction": "keep shape"},
            base_image=(b"reference", "reference.png"),
        )
    routes.update_routes(
        db_session,
        [
            {
                "routeKey": PROMPT_EDIT_4K_ROUTE,
                "provider": "apyi",
                "model": "gemini-3-pro-image-preview-4k",
            }
        ],
    )
    children = db_session.query(Task).filter(Task.batch_id == batch.id).all()
    assert len(children) == 2
    assert float(batch.total_credits_used) == 3
    for child in children:
        assert (
            child.options[AI_MODEL_ROUTES_OPTION_KEY]
            == batch.options[AI_MODEL_ROUTES_OPTION_KEY]
        )
        assert (
            child.options[AI_MODEL_ROUTES_OPTION_KEY][PROMPT_EDIT_4K_ROUTE]["provider"]
            == "krapi"
        )
        assert child.options["secondary_image_url"] == "/files/shared.png"
        assert (
            service.processing_service.with_ai_model_route_snapshot(
                db_session, "prompt_edit", child.options, overwrite=False
            )
            == child.options
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,key",
    [
        ("new", PROMPT_EDIT_2K_ROUTE),
        ("pro_4k", PROMPT_EDIT_4K_ROUTE),
        ("seedream_pro", PROMPT_EDIT_PRO_ROUTE),
    ],
)
async def test_manual_routing_does_not_change_service_credit_cost(
    db_session, mode, key
):
    from app.services.membership_service import MembershipService
    from app.services.service_pricing import resolve_pricing_key

    service = MembershipService()
    await service.initialize_packages(db_session)
    before = {"model": mode}
    after = options(key, model=mode)
    assert await service.calculate_service_cost(
        db_session, "prompt_edit", options=before
    ) == await service.calculate_service_cost(db_session, "prompt_edit", options=after)
    assert resolve_pricing_key("prompt_edit", before) == resolve_pricing_key(
        "prompt_edit", after
    )
