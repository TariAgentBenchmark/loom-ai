#!/usr/bin/env python3
"""
Add agent/invitation code support to the existing database.

Usage:
    uv run python scripts/migrations/20241208_add_agents_invitation_codes.py
    # or
    python scripts/migrations/20241208_add_agents_invitation_codes.py
"""

from __future__ import annotations

import sys
from typing import Callable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.models import Agent, InvitationCode


def get_engine() -> Engine:
    """Build a SQLAlchemy engine based on the current DATABASE_URL."""
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
    """Wrap a SQL statement with IF NOT EXISTS style resilience."""

    def runner(engine: Engine) -> None:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception:
            # Best-effort: ignore if already exists or unsupported
            pass

    return runner


def create_new_tables(engine: Engine) -> None:
    """Create agent/invitation tables if missing."""
    Agent.__table__.create(bind=engine, checkfirst=True)
    InvitationCode.__table__.create(bind=engine, checkfirst=True)
    print("✅ ensured agent and invitation_code tables exist")


def ensure_user_column(
    engine: Engine,
    column_name: str,
    ddl: str,
    fk_stmt: str | None,
    fk_target_table: str | None,
    index_stmt: str,
) -> None:
    """Add a column/index (and FK on non-SQLite) if missing."""
    if column_exists(engine, "users", column_name):
        print(f"ℹ️  users.{column_name} already present")
        return

    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE users ADD COLUMN {ddl}"))
    print(f"✅ added users.{column_name}")

    # Only add FK constraints where supported
    if (
        fk_stmt
        and fk_target_table
        and engine.dialect.name != "sqlite"
        and not fk_exists(engine, "users", column_name, fk_target_table)
    ):
        with engine.begin() as conn:
            conn.execute(text(fk_stmt))
        print(f"✅ added FK for users.{column_name}")

    run_safe(index_stmt)(engine)


def main() -> None:
    engine = get_engine()
    print(f"🏗  Connecting to {settings.database_url}")

    create_new_tables(engine)

    ensure_user_column(
        engine=engine,
        column_name="agent_id",
        ddl="agent_id INTEGER",
        fk_stmt="ALTER TABLE users ADD CONSTRAINT fk_users_agent FOREIGN KEY (agent_id) REFERENCES agents(id)",
        fk_target_table="agents",
        index_stmt="CREATE INDEX ix_users_agent_id ON users (agent_id)",
    )
    ensure_user_column(
        engine=engine,
        column_name="invitation_code_id",
        ddl="invitation_code_id INTEGER",
        fk_stmt="ALTER TABLE users ADD CONSTRAINT fk_users_invitation_code FOREIGN KEY (invitation_code_id) REFERENCES invitation_codes(id)",
        fk_target_table="invitation_codes",
        index_stmt="CREATE INDEX ix_users_invitation_code_id ON users (invitation_code_id)",
    )

    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
