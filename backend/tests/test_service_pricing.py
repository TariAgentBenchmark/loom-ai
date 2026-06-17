from decimal import Decimal

import pytest

from app.services.membership_service import MembershipService
from app.services.service_pricing import resolve_pricing_key, resolve_pricing_target


def test_extract_pattern_combined_t2_resolves_independent_pricing_key():
    assert (
        resolve_pricing_key("extract_pattern", {"pattern_type": "combined_t2"})
        == "extract_pattern_combined_t2_4img"
    )
    assert (
        resolve_pricing_key("extract_pattern", {"pattern_type": "t2"})
        == "extract_pattern_combined_t2_4img"
    )
    assert (
        resolve_pricing_key(
            "extract_pattern",
            {"pattern_type": "combined_t2", "num_images": 1},
        )
        == "extract_pattern_combined_t2_1img"
    )
    assert (
        resolve_pricing_key(
            "extract_pattern",
            {"pattern_type": "combined_t2", "num_images": 2},
        )
        == "extract_pattern_combined_t2_2img"
    )
    assert (
        resolve_pricing_key("extract_pattern", {"pattern_type": "combined"})
        == "extract_pattern_combined"
    )


def test_legacy_extract_pattern_combined_t2_key_stays_independent():
    target = resolve_pricing_target("extract_pattern_combined_t2")

    assert target.service_key == "extract_pattern"
    assert target.variant_key == "combined_t2_4img"
    assert target.pricing_key == "extract_pattern_combined_t2_4img"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("num_images", "expected_cost"),
    [
        (1, Decimal("0.60")),
        (2, Decimal("1.00")),
        (4, Decimal("1.70")),
    ],
)
async def test_combined_t2_cost_uses_variant_price(
    db_session,
    num_images,
    expected_cost,
):
    service = MembershipService()
    await service.initialize_packages(db_session)

    cost = await service.calculate_service_cost(
        db_session,
        "extract_pattern",
        options={"pattern_type": "combined_t2", "num_images": num_images},
    )

    assert cost == expected_cost


@pytest.mark.asyncio
async def test_combined_t2_price_variants_are_seeded(db_session):
    service = MembershipService()
    await service.initialize_packages(db_session)

    prices = await service.get_service_prices(db_session)
    price_map = {
        item["service_key"]: item["price_credits"]
        for item in prices
    }

    assert price_map["extract_pattern_combined_t2_1img"] == 0.6
    assert price_map["extract_pattern_combined_t2_2img"] == 1.0
    assert price_map["extract_pattern_combined_t2_4img"] == 1.7
