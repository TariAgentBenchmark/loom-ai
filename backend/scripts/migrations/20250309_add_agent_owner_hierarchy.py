#!/usr/bin/env python3
"""
Add owner/parent metadata to agents so they can bind to users and support two-level hierarchy.

Usage:
    uv run python scripts/migrations/20250309_add_agent_owner_hierarchy.py
    # or
    python scripts/migrations/20250309_add_agent_owner_hierarchy.py
"""

from __future__ import annotations

import sys
from typing import Callable

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


def fk_exists(engine: Engine, table: str, column: str, referred_table: str) -> bool:
    inspector = inspect(engine)
    for fk in inspector.get_foreign_keys(table):
        if (
            column in fk.get("constrained_columns", [])
            and fk.get("referred_table") == referred_table
        ):
            return True
    return False


def run_safe(stmt: str) -> Callable[[Engine], None]:
    def runner(engine: Engine) -> None:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception:
            # ignore if already applied / not supported
            pass

    return runner


def ensure_agent_column(
    engine: Engine,
    column_name: str,
    ddl: str,
    fk_stmt: str | None,
    fk_target_table: str | None,
    index_stmt: str | None,
    default_stmt: str | None = None,
) -> None:
    if column_exists(engine, "agents", column_name):
        print(f"ℹ️  agents.{column_name} already present")
        return

    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE agents ADD COLUMN {ddl}"))
    print(f"✅ added agents.{column_name}")

    if default_stmt:
        run_safe(default_stmt)(engine)

    if (
        fk_stmt
        and fk_target_table
        and engine.dialect.name != "sqlite"
        and not fk_exists(engine, "agents", column_name, fk_target_table)
    ):
        run_safe(fk_stmt)(engine)

    if index_stmt:
        run_safe(index_stmt)(engine)


def main() -> None:
    engine = get_engine()
    print(f"🏗  Connecting to {settings.database_url}")

    ensure_agent_column(
        engine=engine,
        column_name="owner_user_id",
        ddl="owner_user_id INTEGER",
        fk_stmt="ALTER TABLE agents ADD CONSTRAINT fk_agents_owner FOREIGN KEY (owner_user_id) REFERENCES users(id)",
        fk_target_table="users",
        index_stmt="CREATE INDEX ix_agents_owner_user_id ON agents (owner_user_id)",
    )
    ensure_agent_column(
        engine=engine,
        column_name="parent_agent_id",
        ddl="parent_agent_id INTEGER",
        fk_stmt="ALTER TABLE agents ADD CONSTRAINT fk_agents_parent FOREIGN KEY (parent_agent_id) REFERENCES agents(id)",
        fk_target_table="agents",
        index_stmt="CREATE INDEX ix_agents_parent_agent_id ON agents (parent_agent_id)",
    )
    ensure_agent_column(
        engine=engine,
        column_name="level",
        ddl="level INTEGER DEFAULT 1",
        fk_stmt=None,
        fk_target_table=None,
        index_stmt="CREATE INDEX ix_agents_level ON agents (level)",
        default_stmt="UPDATE agents SET level = 1 WHERE level IS NULL",
    )

    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
