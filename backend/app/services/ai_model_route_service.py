import json
import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

AI_MODEL_ROUTES_SETTING_KEY = "ai_model_routes"
AI_MODEL_ROUTES_OPTION_KEY = "ai_model_routes"
EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY = "extract_pattern.combined.general_2"


class AIModelRouteConfigError(ValueError):
    """Raised when an AI model route config is not supported."""


SUPPORTED_AI_MODEL_ROUTES: Dict[str, Dict[str, Any]] = {
    EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY: {
        "label": "AI提取花型 / 综合模型 / Gemini3 Pro",
        "description": "控制综合模型里 Gemini3 Pro 这一路的服务商；只影响新建任务。",
        "default_provider": "apyi",
        "providers": {
            "apyi": {
                "label": "Apyi",
                "client": "apyi_gemini",
                "models": ["gemini-3-pro-image-preview-4k"],
                "default_model": "gemini-3-pro-image-preview-4k",
                "description": "通过 Apyi 平台调用 Gemini3 Pro 4K 图像模型。",
            },
            "tuzi": {
                "label": "Tuzi",
                "client": "tuzi_gemini",
                "models": ["gemini-3-pro-image-preview-4k"],
                "default_model": "gemini-3-pro-image-preview-4k",
                "description": "通过 Tuzi 平台调用同名 Gemini3 Pro 4K 图像模型。",
            },
        },
    }
}


class AIModelRouteService:
    """Read, validate, and snapshot configurable AI model routes."""

    def _default_selection(self, route_key: str) -> Dict[str, str]:
        definition = self._get_definition(route_key)
        provider = definition["default_provider"]
        provider_definition = definition["providers"][provider]
        return {
            "provider": provider,
            "model": provider_definition["default_model"],
        }

    def _get_definition(self, route_key: str) -> Dict[str, Any]:
        definition = SUPPORTED_AI_MODEL_ROUTES.get(route_key)
        if not definition:
            raise AIModelRouteConfigError(f"不支持的模型路由: {route_key}")
        return definition

    def _normalize_selection(
        self,
        route_key: str,
        raw_selection: Optional[Dict[str, Any]],
        *,
        allow_defaults: bool,
    ) -> Dict[str, str]:
        definition = self._get_definition(route_key)
        if raw_selection is None:
            selection: Dict[str, Any] = {}
        elif isinstance(raw_selection, dict):
            selection = raw_selection
        else:
            raise AIModelRouteConfigError(f"模型路由 {route_key} 配置格式无效")
        default_selection = self._default_selection(route_key)

        raw_provider = selection.get("provider")
        provider = (
            str(raw_provider).strip().lower()
            if raw_provider is not None and str(raw_provider).strip()
            else default_selection["provider"]
            if allow_defaults
            else ""
        )
        if provider not in definition["providers"]:
            raise AIModelRouteConfigError(
                f"模型路由 {route_key} 不支持 provider: {provider or raw_provider}"
            )

        provider_definition = definition["providers"][provider]
        raw_model = selection.get("model")
        model = (
            str(raw_model).strip()
            if raw_model is not None and str(raw_model).strip()
            else provider_definition["default_model"]
            if allow_defaults
            else ""
        )
        if model not in provider_definition["models"]:
            raise AIModelRouteConfigError(
                f"模型路由 {route_key} 的 provider {provider} 不支持模型: {model or raw_model}"
            )

        return {"provider": provider, "model": model}

    def _load_persisted_config(self, db: Session) -> Dict[str, Any]:
        row = (
            db.query(SystemSetting)
            .filter(SystemSetting.key == AI_MODEL_ROUTES_SETTING_KEY)
            .first()
        )
        if not row:
            return {}

        try:
            parsed = json.loads(row.value or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in %s; falling back to defaults", AI_MODEL_ROUTES_SETTING_KEY)
            return {}

        if not isinstance(parsed, dict):
            logger.warning("%s is not a JSON object; falling back to defaults", AI_MODEL_ROUTES_SETTING_KEY)
            return {}
        return parsed

    def get_effective_route(self, db: Session, route_key: str) -> Dict[str, str]:
        persisted = self._load_persisted_config(db)
        try:
            return self._normalize_selection(
                route_key,
                persisted.get(route_key) if isinstance(persisted, dict) else None,
                allow_defaults=True,
            )
        except AIModelRouteConfigError as exc:
            logger.warning("Invalid persisted AI model route %s: %s", route_key, exc)
            return self._default_selection(route_key)

    def get_admin_routes(self, db: Session) -> Dict[str, List[Dict[str, Any]]]:
        routes: List[Dict[str, Any]] = []
        for route_key, definition in SUPPORTED_AI_MODEL_ROUTES.items():
            selection = self.get_effective_route(db, route_key)
            providers = []
            for provider_key, provider_definition in definition["providers"].items():
                providers.append(
                    {
                        "provider": provider_key,
                        "label": provider_definition["label"],
                        "client": provider_definition["client"],
                        "models": list(provider_definition["models"]),
                        "defaultModel": provider_definition["default_model"],
                        "description": provider_definition.get("description"),
                    }
                )
            routes.append(
                {
                    "routeKey": route_key,
                    "label": definition["label"],
                    "description": definition.get("description"),
                    "provider": selection["provider"],
                    "model": selection["model"],
                    "providers": providers,
                }
            )
        return {"routes": routes}

    def update_routes(
        self,
        db: Session,
        route_updates: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        next_config: Dict[str, Dict[str, str]] = {}
        for route_key in SUPPORTED_AI_MODEL_ROUTES:
            next_config[route_key] = self.get_effective_route(db, route_key)

        for item in route_updates:
            route_key = str(item.get("routeKey") or item.get("route_key") or "").strip()
            if not route_key:
                raise AIModelRouteConfigError("模型路由不能为空")
            if route_key not in SUPPORTED_AI_MODEL_ROUTES:
                raise AIModelRouteConfigError(f"不支持的模型路由: {route_key}")

            next_config[route_key] = self._normalize_selection(
                route_key,
                {
                    "provider": item.get("provider"),
                    "model": item.get("model"),
                },
                allow_defaults=True,
            )

        row = (
            db.query(SystemSetting)
            .filter(SystemSetting.key == AI_MODEL_ROUTES_SETTING_KEY)
            .first()
        )
        serialized = json.dumps(next_config, ensure_ascii=False, sort_keys=True)
        if row:
            row.value = serialized
            row.description = "AI模型路由配置"
        else:
            db.add(
                SystemSetting(
                    key=AI_MODEL_ROUTES_SETTING_KEY,
                    value=serialized,
                    description="AI模型路由配置",
                )
            )
        db.commit()
        return self.get_admin_routes(db)

    def _routes_for_task(self, task_type: str, options: Dict[str, Any]) -> List[str]:
        if task_type != "extract_pattern":
            return []

        pattern_type = (
            str(options.get("pattern_type") or "general_1")
            .strip()
            .lower()
            .replace("-", "_")
        )
        if pattern_type in {"combined", "composite"}:
            return [EXTRACT_PATTERN_COMBINED_GENERAL2_ROUTE_KEY]
        return []

    def apply_route_snapshot(
        self,
        db: Session,
        task_type: str,
        options: Optional[Dict[str, Any]],
        *,
        overwrite: bool,
    ) -> Dict[str, Any]:
        next_options = dict(options or {})
        route_keys = self._routes_for_task(task_type, next_options)
        if not route_keys:
            return next_options

        existing_routes = next_options.get(AI_MODEL_ROUTES_OPTION_KEY)
        route_snapshots: Dict[str, Any] = (
            deepcopy(existing_routes) if isinstance(existing_routes, dict) else {}
        )

        for route_key in route_keys:
            if overwrite or route_key not in route_snapshots:
                route_snapshots[route_key] = self.get_effective_route(db, route_key)
            else:
                route_snapshots[route_key] = self._normalize_selection(
                    route_key,
                    route_snapshots[route_key],
                    allow_defaults=False,
                )

        next_options[AI_MODEL_ROUTES_OPTION_KEY] = route_snapshots
        return next_options

    @classmethod
    def resolve_snapshot_from_options(
        cls,
        options: Optional[Dict[str, Any]],
        route_key: str,
    ) -> Dict[str, str]:
        service = cls()
        route_options = (options or {}).get(AI_MODEL_ROUTES_OPTION_KEY)
        if not isinstance(route_options, dict) or route_key not in route_options:
            return service._default_selection(route_key)

        return service._normalize_selection(
            route_key,
            route_options[route_key],
            allow_defaults=False,
        )
