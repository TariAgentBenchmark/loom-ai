"""Service pricing helpers for variant-aware costs."""

from dataclasses import dataclass
import re
from typing import Any, Dict, Optional

PATTERN_VARIANTS = {
    "general_1_1img",
    "general_1_2img",
    "general_1_4img",
    "combined",
    "denim",
}
UPSCALE_VARIANTS = {"meitu_v2", "runninghub_vr2"}


def _normalize_pattern_type(raw_value: Optional[str]) -> Optional[str]:
    """Normalize pattern type to supported pricing variants."""
    normalized = (raw_value or "").strip().lower().replace("-", "_")

    if re.match(r"general_?1_\d+img", normalized):
        return "general_1"

    if normalized in {
        "general",
        "general1",
        "general_1",
        "general2",
        "general_2",
        "general_model",
    }:
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
        legacy = service_key[len("extract_pattern_") :]
        if legacy == "general_1":
            legacy = "general_1_4img"
        return "extract_pattern", legacy
    if service_key.startswith("upscale_"):
        return "upscale", service_key[len("upscale_") :]
    return service_key, None


def _normalize_num_images(raw_value: Optional[Any]) -> Optional[int]:
    if raw_value is None:
        return None
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None
    return value if value in {1, 2, 4} else None


def _extract_general_image_count(raw_value: Optional[str]) -> Optional[int]:
    if not raw_value:
        return None
    normalized = str(raw_value).strip().lower().replace("-", "_")
    match = re.match(r"general_?1_(\d)img", normalized)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


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
        num_images = _normalize_num_images(
            opts.get("num_images") or opts.get("numImages")
        )
        count_from_pattern = _extract_general_image_count(raw_pattern)
        if count_from_pattern is not None:
            num_images = count_from_pattern

        pattern_type = _normalize_pattern_type(raw_pattern) or "general_1"
        if pattern_type == "general_1":
            count = num_images or 4
            variant_key = f"general_1_{count}img"
        else:
            variant_key = pattern_type

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
