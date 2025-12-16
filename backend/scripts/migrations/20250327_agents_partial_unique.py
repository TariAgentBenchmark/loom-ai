#!/usr/bin/env python3
"""
Switch agents.name to a partial unique index (only active rows) so soft-deleted agents
can reuse names.

Usage:
    uv run python scripts/migrations/20250327_agents_partial_unique.py
    # or
    python scripts/migrations/20250327_agents_partial_unique.py
"""
from __future__ import annotations

import sys
from typing import Sequence, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import settings


def get_engine() -> Engine:
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 20},
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


def find_active_duplicates(engine: Engine) -> Sequence[Tuple[str, int]]:
    """Return (name, count) where active (is_deleted=false) agents share the same name."""
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT name, COUNT(*) AS cnt
                FROM agents
                WHERE is_deleted = false
                GROUP BY name
                HAVING COUNT(*) > 1
                """
            )
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def apply_partial_unique_index(engine: Engine) -> None:
    if engine.dialect.name == "sqlite":
        print("ℹ️ SQLite detected; skipping index change (global unique constraint remains).")
        return

    duplicates = find_active_duplicates(engine)
    if duplicates:
        dup_msg = "; ".join(f"{name} (x{cnt})" for name, cnt in duplicates)
        raise RuntimeError(
            f"Found duplicate active agent names, aborting index creation: {dup_msg}"
        )

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_name_key"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS agents_name_active_idx "
                "ON agents (name) WHERE is_deleted = false"
            )
        )
    print("✅ applied partial unique index on agents.name (is_deleted = false)")


def main() -> None:
    engine = get_engine()
    print(f"🏗  Connecting to {settings.database_url}")
    apply_partial_unique_index(engine)
    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
