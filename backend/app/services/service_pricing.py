"""Service pricing helpers for variant-aware costs."""

from typing import Any, Dict, Optional


def _normalize_pattern_type(raw_value: Optional[str]) -> str:
    """Normalize pattern type to the canonical identifiers used internally."""
    normalized = (raw_value or "general_2").strip().lower().replace("-", "_")

    if normalized == "general":
        return "general_2"

    if normalized.startswith("general") and normalized[-1].isdigit():
        return f"general_{normalized[-1]}"

    return normalized or "general_2"


def _normalize_upscale_engine(raw_value: Optional[str]) -> str:
    """Normalize upscale engine names to known identifiers."""
    normalized = (raw_value or "meitu_v2").strip().lower()
    if normalized not in {"meitu_v2", "runninghub_vr2"}:
        return "meitu_v2"
    return normalized


def resolve_pricing_key(service_key: str, options: Optional[Dict[str, Any]] = None) -> str:
    """
    Build a pricing key that captures service variants (pattern types, upscale engines, etc).
    Falls back to the base service key for services without variants.
    """
    opts = options or {}

    if service_key == "extract_pattern":
        pattern_type = _normalize_pattern_type(opts.get("pattern_type"))
        return f"{service_key}_{pattern_type}"

    if service_key == "upscale":
        engine = _normalize_upscale_engine(opts.get("engine") or opts.get("upscale_engine"))
        return f"{service_key}_{engine}"

    return service_key
