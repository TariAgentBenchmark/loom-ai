from decimal import Decimal

import pytest

from app.services.membership_service import MembershipService
from app.services.service_pricing import resolve_pricing_key, resolve_pricing_target


def test_extract_pattern_combined_t2_resolves_independent_pricing_key():
    assert (
        resolve_pricing_key("extract_pattern", {"pattern_type": "combined_t2"})
        == "extract_pattern_combined_t2"
    )
    assert (
        resolve_pricing_key("extract_pattern", {"pattern_type": "t2"})
        == "extract_pattern_combined_t2"
    )
    assert (
        resolve_pricing_key("extract_pattern", {"pattern_type": "combined"})
        == "extract_pattern_combined"
    )


def test_legacy_extract_pattern_combined_t2_key_stays_independent():
    target = resolve_pricing_target("extract_pattern_combined_t2")

    assert target.service_key == "extract_pattern"
    assert target.variant_key == "combined_t2"
    assert target.pricing_key == "extract_pattern_combined_t2"


@pytest.mark.asyncio
async def test_combined_t2_cost_uses_variant_price(db_session):
    service = MembershipService()
    await service.initialize_packages(db_session)

    cost = await service.calculate_service_cost(
        db_session,
        "extract_pattern",
        options={"pattern_type": "combined_t2"},
    )

    assert cost == Decimal("1.70")
