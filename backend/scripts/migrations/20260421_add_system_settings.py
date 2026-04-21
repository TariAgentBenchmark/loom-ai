#!/usr/bin/env python3
"""
Create system_settings table for admin-managed key/value settings.

Usage:
    python scripts/migrations/20260421_add_system_settings.py
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, inspect, text

from app.core.config import settings


def get_engine():
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 20},
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


def main() -> None:
    engine = get_engine()
    inspector = inspect(engine)
    if inspector.has_table("system_settings"):
        print("ℹ️  system_settings already exists")
        return

    ddl = """
    CREATE TABLE system_settings (
        id INTEGER PRIMARY KEY,
        key VARCHAR(100) NOT NULL UNIQUE,
        value TEXT NOT NULL,
        description VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    index_ddl = "CREATE UNIQUE INDEX IF NOT EXISTS ix_system_settings_key ON system_settings (key)"

    with engine.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(text(index_ddl))

    print("✅ system_settings created")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
