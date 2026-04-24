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
