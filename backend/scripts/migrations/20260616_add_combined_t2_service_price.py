#!/usr/bin/env python3
"""
Add independent pricing for extract_pattern combined_t2 and refresh old defaults.

Usage:
    uv run python scripts/migrations/20260616_add_combined_t2_service_price.py
    python scripts/migrations/20260616_add_combined_t2_service_price.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings


def get_engine() -> Engine:
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 20},
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


def _decimal_or_none(value: object) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def _should_update(
    current_value: object,
    *,
    old_defaults: Iterable[str],
) -> bool:
    current = _decimal_or_none(current_value)
    if current is None:
        return True
    return current in {Decimal(value) for value in old_defaults}


def upsert_extract_pattern_variant(
    conn,
    *,
    variant_key: str,
    variant_name: str,
    description: str,
    price_credits: str,
    old_defaults: Iterable[str],
) -> bool:
    row = conn.execute(
        text(
            """
            SELECT id, price_credits
            FROM service_price_variants
            WHERE parent_service_key = 'extract_pattern'
              AND variant_key = :variant_key
            """
        ),
        {"variant_key": variant_key},
    ).fetchone()

    if row is None:
        conn.execute(
            text(
                """
                INSERT INTO service_price_variants (
                    parent_service_key,
                    variant_key,
                    variant_name,
                    description,
                    price_credits,
                    active,
                    created_at,
                    updated_at
                ) VALUES (
                    'extract_pattern',
                    :variant_key,
                    :variant_name,
                    :description,
                    :price_credits,
                    TRUE,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "variant_key": variant_key,
                "variant_name": variant_name,
                "description": description,
                "price_credits": price_credits,
            },
        )
        return True

    updates = {
        "variant_key": variant_key,
        "variant_name": variant_name,
        "description": description,
    }
    set_price = _should_update(row[1], old_defaults=old_defaults)

    if set_price:
        conn.execute(
            text(
                """
                UPDATE service_price_variants
                SET variant_name = :variant_name,
                    description = :description,
                    price_credits = :price_credits,
                    updated_at = CURRENT_TIMESTAMP
                WHERE parent_service_key = 'extract_pattern'
                  AND variant_key = :variant_key
                """
            ),
            {**updates, "price_credits": price_credits},
        )
    else:
        conn.execute(
            text(
                """
                UPDATE service_price_variants
                SET variant_name = :variant_name,
                    description = :description,
                    updated_at = CURRENT_TIMESTAMP
                WHERE parent_service_key = 'extract_pattern'
                  AND variant_key = :variant_key
                """
            ),
            updates,
        )

    return set_price


def main() -> None:
    engine = get_engine()
    inspector = inspect(engine)

    if not inspector.has_table("service_price_variants"):
        print("❌ service_price_variants table does not exist")
        return

    variants = [
        {
            "variant_key": "general_1_1img",
            "variant_name": "通用模型-1张图",
            "description": "AI提取花型（通用模型，输出1张图）",
            "price_credits": "0.6",
            "old_defaults": ["0.4"],
        },
        {
            "variant_key": "general_1_2img",
            "variant_name": "通用模型-2张图",
            "description": "AI提取花型（通用模型，输出2张图）",
            "price_credits": "1.0",
            "old_defaults": ["0.75"],
        },
        {
            "variant_key": "combined",
            "variant_name": "综合模型",
            "description": "AI提取花型（综合模型，并行多模型输出3图）",
            "price_credits": "1.7",
            "old_defaults": ["1.5"],
        },
        {
            "variant_key": "combined_t2",
            "variant_name": "综合T2",
            "description": "AI提取花型（综合T2，输出3张2K图和1张4K图）",
            "price_credits": "1.7",
            "old_defaults": ["1.5"],
        },
    ]

    changed = 0
    with engine.begin() as conn:
        for variant in variants:
            if upsert_extract_pattern_variant(conn, **variant):
                changed += 1

    print(f"✅ Service variant prices refreshed, changed {changed} rows")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
