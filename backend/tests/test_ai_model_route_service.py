import pytest

from app.services.ai_model_route_service import (
    AI_MODEL_ROUTES_OPTION_KEY,
    EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
    AIModelRouteConfigError,
    AIModelRouteService,
)


def test_ai_model_route_service_defaults_to_apyi(db_session):
    service = AIModelRouteService()

    data = service.get_admin_routes(db_session)
    route = data["routes"][0]

    assert route["routeKey"] == EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY
    assert route["provider"] == "apyi"
    assert route["model"] == "gemini-3-pro-image-preview-4k"
    assert {option["provider"] for option in route["providers"]} == {"apyi", "tuzi"}
    expected_models = [
        "gemini-3-pro-image-preview-4k",
        "gemini-3-pro-image-preview-2k",
        "gemini-3.1-flash-image-preview-4k",
        "gemini-3.1-flash-image-preview-2k",
    ]
    apyi_provider = next(
        option for option in route["providers"] if option["provider"] == "apyi"
    )
    tuzi_provider = next(
        option for option in route["providers"] if option["provider"] == "tuzi"
    )
    assert apyi_provider["models"] == expected_models
    assert tuzi_provider["models"] == expected_models


def test_ai_model_route_service_updates_and_snapshots_tuzi(db_session):
    service = AIModelRouteService()

    service.update_routes(
        db_session,
        [
            {
                "routeKey": EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
                "provider": "tuzi",
                "model": "gemini-3-pro-image-preview-4k",
            }
        ],
    )

    options = service.apply_route_snapshot(
        db_session,
        "extract_pattern",
        {"pattern_type": "combined"},
        overwrite=True,
    )

    assert options[AI_MODEL_ROUTES_OPTION_KEY] == {
        EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY: {
            "provider": "tuzi",
            "model": "gemini-3-pro-image-preview-4k",
        }
    }


def test_ai_model_route_service_resolves_tuzi_nano_banana_2_runtime(db_session):
    service = AIModelRouteService()

    service.update_routes(
        db_session,
        [
            {
                "routeKey": EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
                "provider": "tuzi",
                "model": "gemini-3.1-flash-image-preview-2k",
            }
        ],
    )

    options = service.apply_route_snapshot(
        db_session,
        "extract_pattern",
        {"pattern_type": "combined"},
        overwrite=True,
    )

    runtime = AIModelRouteService.resolve_runtime_from_options(
        options,
        EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
    )

    assert runtime == {
        "provider": "tuzi",
        "model": "gemini-3.1-flash-image-preview-2k",
        "api_model": "gemini-3.1-flash-image-preview",
        "resolution": "2K",
    }


def test_ai_model_route_service_resolves_apyi_pro_2k_runtime(db_session):
    service = AIModelRouteService()

    service.update_routes(
        db_session,
        [
            {
                "routeKey": EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
                "provider": "apyi",
                "model": "gemini-3-pro-image-preview-2k",
            }
        ],
    )

    options = service.apply_route_snapshot(
        db_session,
        "extract_pattern",
        {"pattern_type": "combined"},
        overwrite=True,
    )

    runtime = AIModelRouteService.resolve_runtime_from_options(
        options,
        EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
    )

    assert runtime == {
        "provider": "apyi",
        "model": "gemini-3-pro-image-preview-2k",
        "api_model": "gemini-3-pro-image-preview",
        "resolution": "2K",
    }


def test_ai_model_route_service_rejects_unsupported_provider(db_session):
    service = AIModelRouteService()

    with pytest.raises(AIModelRouteConfigError):
        service.update_routes(
            db_session,
            [
                {
                    "routeKey": EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY,
                    "provider": "unknown",
                    "model": "gemini-3-pro-image-preview-4k",
                }
            ],
        )
