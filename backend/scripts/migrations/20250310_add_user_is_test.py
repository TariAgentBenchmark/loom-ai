#!/usr/bin/env python3
"""
Add is_test_user flag to users.
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


def column_exists(engine: Engine, table: str, column: str) -> bool:
    inspector = inspect(engine)
    return any(col["name"] == column for col in inspector.get_columns(table))


def main() -> None:
    engine = get_engine()
    if column_exists(engine, "users", "is_test_user"):
        print("ℹ️  users.is_test_user already exists")
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_test_user BOOLEAN DEFAULT FALSE"))
    print("✅ Added users.is_test_user")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
