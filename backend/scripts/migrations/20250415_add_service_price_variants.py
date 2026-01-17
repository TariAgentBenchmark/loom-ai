#!/usr/bin/env python3
"""
Create service_price_variants table and migrate legacy variant rows.
"""

from __future__ import annotations

import sys
from typing import Dict, Tuple

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    inspect,
    text,
)
from sqlalchemy.engine import Engine

from app.core.config import settings


SKIP_PATTERN_VARIANTS = {"general_2", "positioning", "fine"}
GENERAL_4IMG_KEY = "general_1_4img"


def get_engine() -> Engine:
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 20},
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


def table_exists(engine: Engine, table: str) -> bool:
    inspector = inspect(engine)
    return table in inspector.get_table_names()


def create_variants_table(engine: Engine) -> None:
    metadata = MetaData()
    Table(
        "service_price_variants",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("parent_service_key", String(50), nullable=False, index=True),
        Column("variant_key", String(50), nullable=False),
        Column("variant_name", String(100), nullable=False),
        Column("description", Text),
        Column("price_credits", Numeric(18, 2)),
        Column("active", Boolean, server_default=text("TRUE")),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), server_default=func.now()),
        UniqueConstraint("parent_service_key", "variant_key", name="uq_service_variant"),
    )
    metadata.create_all(bind=engine)


def parse_variant(service_key: str) -> Tuple[str, str]:
    if service_key.startswith("extract_pattern_"):
        return "extract_pattern", service_key[len("extract_pattern_") :]
    if service_key.startswith("upscale_"):
        return "upscale", service_key[len("upscale_") :]
    raise ValueError(f"Unsupported variant key: {service_key}")


def main() -> None:
    engine = get_engine()

    if not table_exists(engine, "service_prices"):
        print("❌ service_prices table does not exist")
        return

    if not table_exists(engine, "service_price_variants"):
        create_variants_table(engine)
        print("✅ Created service_price_variants table")
    else:
        print("ℹ️  service_price_variants already exists")

    with engine.begin() as conn:
        parent_rows = conn.execute(
            text(
                """
                SELECT service_key, service_name, price_credits
                FROM service_prices
                WHERE service_key IN ('extract_pattern', 'upscale')
                """
            )
        ).fetchall()
        parent_info: Dict[str, Tuple[str, float]] = {
            row[0]: (row[1], row[2]) for row in parent_rows
        }

        existing_variants = conn.execute(
            text(
                """
                SELECT parent_service_key, variant_key
                FROM service_price_variants
                """
            )
        ).fetchall()
        existing_keys = {(row[0], row[1]) for row in existing_variants}

        if ("extract_pattern", "general_1") in existing_keys:
            if ("extract_pattern", GENERAL_4IMG_KEY) not in existing_keys:
                conn.execute(
                    text(
                        """
                        UPDATE service_price_variants
                        SET variant_key = :new_key,
                            variant_name = CASE
                                WHEN variant_name IS NULL OR variant_name = '' OR variant_name = '通用模型' THEN :new_name
                                ELSE variant_name
                            END,
                            description = CASE
                                WHEN description IS NULL OR description = '' OR description LIKE '%通用模型%' THEN :new_desc
                                ELSE description
                            END
                        WHERE parent_service_key = 'extract_pattern'
                          AND variant_key = 'general_1'
                        """
                    ),
                    {
                        "new_key": GENERAL_4IMG_KEY,
                        "new_name": "通用模型-4张图",
                        "new_desc": "AI提取花型（通用模型，输出4张图）",
                    },
                )
                existing_keys.discard(("extract_pattern", "general_1"))
                existing_keys.add(("extract_pattern", GENERAL_4IMG_KEY))
            else:
                conn.execute(
                    text(
                        """
                        UPDATE service_price_variants AS target
                        SET price_credits = COALESCE(target.price_credits, source.price_credits)
                        FROM service_price_variants AS source
                        WHERE target.parent_service_key = 'extract_pattern'
                          AND target.variant_key = :new_key
                          AND source.parent_service_key = 'extract_pattern'
                          AND source.variant_key = 'general_1'
                        """
                    ),
                    {"new_key": GENERAL_4IMG_KEY},
                )
                conn.execute(
                    text(
                        """
                        DELETE FROM service_price_variants
                        WHERE parent_service_key = 'extract_pattern'
                          AND variant_key = 'general_1'
                        """
                    )
                )
                existing_keys.discard(("extract_pattern", "general_1"))

        legacy_rows = conn.execute(
            text(
                """
                SELECT service_id, service_key, service_name, description, price_credits, active, created_at, updated_at
                FROM service_prices
                WHERE service_key LIKE 'extract_pattern_%'
                   OR service_key LIKE 'upscale_%'
                """
            )
        ).fetchall()

        migrated = 0
        skipped = 0
        for row in legacy_rows:
            service_key = row[1]
            parent_key, variant_key = parse_variant(service_key)

            if parent_key == "extract_pattern" and variant_key in SKIP_PATTERN_VARIANTS:
                skipped += 1
                continue

            if parent_key == "extract_pattern" and variant_key == "general_1":
                variant_key = GENERAL_4IMG_KEY

            key = (parent_key, variant_key)
            if key in existing_keys:
                continue

            parent_name, parent_price = parent_info.get(parent_key, (None, None))
            variant_price = row[4]
            price_to_store = (
                None if parent_price is not None and variant_price == parent_price else variant_price
            )

            variant_name = row[2] or variant_key
            if parent_name and variant_name.startswith(f"{parent_name}-"):
                variant_name = variant_name[len(parent_name) + 1 :]

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
                        :parent_service_key,
                        :variant_key,
                        :variant_name,
                        :description,
                        :price_credits,
                        :active,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "parent_service_key": parent_key,
                    "variant_key": variant_key,
                    "variant_name": variant_name,
                    "description": row[3],
                    "price_credits": price_to_store,
                    "active": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                },
            )
            migrated += 1

        conn.execute(
            text(
                """
                DELETE FROM service_prices
                WHERE service_key LIKE 'extract_pattern_%'
                   OR service_key LIKE 'upscale_%'
                """
            )
        )

        print(f"✅ Migrated {migrated} variant rows, skipped {skipped} legacy modes")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
