#!/usr/bin/env python3
"""
Add agent_id_snapshot column to orders and backfill existing data.
"""

from __future__ import annotations

import sys
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


def table_exists(engine: Engine, table: str) -> bool:
    inspector = inspect(engine)
    return table in inspector.get_table_names()


def column_exists(engine: Engine, table: str, column: str) -> bool:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return False
    return column in {col["name"] for col in inspector.get_columns(table)}


def main() -> None:
    engine = get_engine()
    if not table_exists(engine, "orders"):
        print("❌ orders table does not exist")
        return

    with engine.begin() as conn:
        if not column_exists(engine, "orders", "agent_id_snapshot"):
            conn.execute(text("ALTER TABLE orders ADD COLUMN agent_id_snapshot INTEGER"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_orders_agent_id_snapshot ON orders (agent_id_snapshot)")
            )
            print("✅ Added orders.agent_id_snapshot column")
        else:
            print("ℹ️  orders.agent_id_snapshot already exists")

        # Backfill snapshot for existing orders
        conn.execute(
            text(
                """
                UPDATE orders
                SET agent_id_snapshot = (
                    SELECT users.agent_id FROM users WHERE users.id = orders.user_id
                )
                WHERE agent_id_snapshot IS NULL
                """
            )
        )
        print("✅ Backfilled orders.agent_id_snapshot for existing orders")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
