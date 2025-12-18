#!/usr/bin/env python3
"""
Add agent referral link support to the existing database.

Usage:
    uv run python scripts/migrations/20250401_add_agent_referral_links.py
    # or
    python scripts/migrations/20250401_add_agent_referral_links.py
"""

from __future__ import annotations

import sys
import secrets
import string
from typing import Callable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.models import AgentReferralLink


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
    """Create agent referral link table if missing."""
    AgentReferralLink.__table__.create(bind=engine, checkfirst=True)
    print("✅ ensured agent_referral_links table exists")


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


def _generate_referral_token(length: int = 12) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def seed_referral_links(engine: Engine) -> None:
    """Create a referral link for existing agents if missing."""
    with engine.begin() as conn:
        agent_rows = conn.execute(
            text("SELECT id FROM agents WHERE is_deleted = false")
        ).fetchall()
        if not agent_rows:
            print("ℹ️  no active agents found, skipping seed")
            return

        existing = conn.execute(
            text(
                "SELECT DISTINCT agent_id FROM agent_referral_links WHERE is_deleted = false"
            )
        ).fetchall()
        existing_ids = {row[0] for row in existing}

        created = 0
        for (agent_id,) in agent_rows:
            if agent_id in existing_ids:
                continue

            token = _generate_referral_token()
            while conn.execute(
                text("SELECT 1 FROM agent_referral_links WHERE token = :token"),
                {"token": token},
            ).first():
                token = _generate_referral_token()

            conn.execute(
                text(
                    """
                    INSERT INTO agent_referral_links
                        (token, agent_id, status, usage_count, is_deleted)
                    VALUES
                        (:token, :agent_id, :status, :usage_count, :is_deleted)
                    """
                ),
                {
                    "token": token,
                    "agent_id": agent_id,
                    "status": "ACTIVE",
                    "usage_count": 0,
                    "is_deleted": False,
                },
            )
            created += 1

        print(f"✅ seeded {created} agent referral link(s)")


def main() -> None:
    engine = get_engine()
    print(f"🏗  Connecting to {settings.database_url}")

    create_new_tables(engine)

    ensure_user_column(
        engine=engine,
        column_name="agent_referral_link_id",
        ddl="agent_referral_link_id INTEGER",
        fk_stmt="ALTER TABLE users ADD CONSTRAINT fk_users_agent_referral_link FOREIGN KEY (agent_referral_link_id) REFERENCES agent_referral_links(id)",
        fk_target_table="agent_referral_links",
        index_stmt="CREATE INDEX ix_users_agent_referral_link_id ON users (agent_referral_link_id)",
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE agent_referral_links
                SET status = 'ACTIVE'
                WHERE status = 'active'
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE agent_referral_links
                SET status = 'DISABLED'
                WHERE status = 'disabled'
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE agent_referral_links
                SET status = 'EXPIRED'
                WHERE status = 'expired'
                """
            )
        )

    seed_referral_links(engine)
    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
