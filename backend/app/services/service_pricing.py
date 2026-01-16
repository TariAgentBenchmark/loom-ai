"""Service pricing helpers for variant-aware costs."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

PATTERN_VARIANTS = {"general_1", "combined", "denim"}
UPSCALE_VARIANTS = {"meitu_v2", "runninghub_vr2"}


def _normalize_pattern_type(raw_value: Optional[str]) -> Optional[str]:
    """Normalize pattern type to supported pricing variants."""
    normalized = (raw_value or "").strip().lower().replace("-", "_")

    if normalized in {"general", "general1", "general_1", "general2", "general_2", "general_model"}:
        return "general_1"

    if normalized in {"combined", "composite"}:
        return "combined"

    if normalized == "denim":
        return "denim"

    return None


def _normalize_upscale_engine(raw_value: Optional[str]) -> Optional[str]:
    """Normalize upscale engine names to known identifiers."""
    if raw_value is None:
        return "meitu_v2"
    normalized = str(raw_value).strip().lower()
    if normalized not in UPSCALE_VARIANTS:
        return "meitu_v2"
    return normalized


def _split_legacy_variant_key(service_key: str) -> tuple[str, Optional[str]]:
    if service_key.startswith("extract_pattern_"):
        return "extract_pattern", service_key[len("extract_pattern_") :]
    if service_key.startswith("upscale_"):
        return "upscale", service_key[len("upscale_") :]
    return service_key, None


@dataclass(frozen=True)
class PricingTarget:
    service_key: str
    variant_key: Optional[str]
    pricing_key: str


def resolve_pricing_target(
    service_key: str, options: Optional[Dict[str, Any]] = None
) -> PricingTarget:
    """
    Resolve base service key + variant key for pricing, supporting legacy composite keys.
    """
    opts = options or {}
    base_key, legacy_variant = _split_legacy_variant_key(service_key)
    variant_key = legacy_variant

    if base_key == "extract_pattern":
        raw_pattern = opts.get("pattern_type", legacy_variant)
        if raw_pattern is None:
            variant_key = "general_1"
        else:
            variant_key = _normalize_pattern_type(raw_pattern)

    if base_key == "upscale":
        raw_engine = opts.get("engine") or opts.get("upscale_engine") or legacy_variant
        variant_key = _normalize_upscale_engine(raw_engine)

    if variant_key and base_key == "extract_pattern" and variant_key not in PATTERN_VARIANTS:
        variant_key = None
    if variant_key and base_key == "upscale" and variant_key not in UPSCALE_VARIANTS:
        variant_key = None

    pricing_key = f"{base_key}_{variant_key}" if variant_key else base_key
    return PricingTarget(base_key, variant_key, pricing_key)


def resolve_pricing_key(service_key: str, options: Optional[Dict[str, Any]] = None) -> str:
    """Return a legacy composite pricing key string for logging/debugging."""
    return resolve_pricing_target(service_key, options).pricing_key
