import httpx
import pytest
from app.core.database import get_db
from app.main import app
from app.models.user import User, UserStatus
from app.services.ai_model_route_service import AIModelRouteService
from app.services.ai_route_catalog import PROMPT_EDIT_4K_ROUTE
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_manual_route_api_is_admin_only_and_preserves_capability_metadata(
    db_session, monkeypatch
):
    from app.core.config import settings

    monkeypatch.setattr(settings, "krapi_api_key", "offline-secret-not-for-frontend")
    normal = User(
        user_id="route-normal",
        phone="qa-route-normal",
        hashed_password="unused",
        status=UserStatus.ACTIVE,
        is_admin=False,
        credits=0,
    )
    admin = User(
        user_id="route-admin",
        phone="qa-route-admin",
        hashed_password="unused",
        status=UserStatus.ACTIVE,
        is_admin=True,
        credits=0,
    )
    db_session.add_all([normal, admin])
    db_session.commit()
    auth = AuthService()
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            for method in ("GET", "PUT"):
                headers = {
                    "Authorization": "Bearer "
                    + auth.create_access_token({"sub": normal.user_id})
                }
                kwargs = {"json": {"routes": []}} if method == "PUT" else {}
                response = await client.request(
                    method, "/v1/admin/ai-model-routes", headers=headers, **kwargs
                )
                assert response.status_code == 403
            headers = {
                "Authorization": "Bearer "
                + auth.create_access_token(
                    {"sub": admin.user_id, "admin_session": True}
                )
            }
            response = await client.get("/v1/admin/ai-model-routes", headers=headers)
            assert response.status_code == 200
            routes = response.json()["data"]["routes"]
            assert (
                next(r for r in routes if r["routeKey"] == "expand_image")["readOnly"]
                is True
            )
            route = next(r for r in routes if r["routeKey"] == PROMPT_EDIT_4K_ROUTE)
            assert (
                next(p for p in route["providers"] if p["provider"] == "krapi")[
                    "configured"
                ]
                is True
            )
            assert "offline-secret-not-for-frontend" not in response.text
            changed = await client.put(
                "/v1/admin/ai-model-routes",
                headers=headers,
                json={
                    "routes": [
                        {
                            "routeKey": PROMPT_EDIT_4K_ROUTE,
                            "provider": "krapi",
                            "model": "T香蕉pro",
                        }
                    ]
                },
            )
            assert changed.status_code == 200
            assert (
                AIModelRouteService().get_effective_route(
                    db_session, PROMPT_EDIT_4K_ROUTE
                )["provider"]
                == "krapi"
            )
            rejected = await client.put(
                "/v1/admin/ai-model-routes",
                headers=headers,
                json={
                    "routes": [
                        {
                            "routeKey": PROMPT_EDIT_4K_ROUTE,
                            "provider": "seedream",
                            "model": "seedream",
                        }
                    ]
                },
            )
            assert rejected.status_code == 400
    finally:
        app.dependency_overrides.pop(get_db, None)
