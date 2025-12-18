#!/usr/bin/env python3
"""
Add agent.commission_mode and ensure referral links exist.

Usage:
    uv run python scripts/migrations/20250402_add_agent_commission_mode_and_links.py
    # or
    python scripts/migrations/20250402_add_agent_commission_mode_and_links.py
"""

from __future__ import annotations

import sys
import secrets
import string
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
            pass

    return runner


def ensure_commission_mode(engine: Engine) -> None:
    if column_exists(engine, "agents", "commission_mode"):
        print("ℹ️  agents.commission_mode already present")
    else:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE agents ADD COLUMN commission_mode VARCHAR(20) DEFAULT 'TIERED'")
            )
        print("✅ added agents.commission_mode")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE agents
                SET commission_mode = 'TIERED'
                WHERE commission_mode IS NULL
                """
            )
        )
    print("✅ backfilled commission_mode to 'TIERED'")


def ensure_referral_links(engine: Engine) -> None:
    if not column_exists(engine, "agent_referral_links", "id"):
        from app.models.agent import AgentReferralLink  # noqa: WPS433

        AgentReferralLink.__table__.create(bind=engine, checkfirst=True)
        print("✅ created agent_referral_links table")

    with engine.begin() as conn:
        agent_rows = conn.execute(
            text("SELECT id FROM agents WHERE is_deleted = false")
        ).fetchall()
        existing = conn.execute(
            text(
                "SELECT DISTINCT agent_id FROM agent_referral_links WHERE is_deleted = false"
            )
        ).fetchall()
        existing_ids = {row[0] for row in existing}

        def gen_token(length: int = 12) -> str:
            alphabet = string.ascii_uppercase + string.digits
            return "".join(secrets.choice(alphabet) for _ in range(length))

        created = 0
        for (agent_id,) in agent_rows:
            if agent_id in existing_ids:
                continue
            token = gen_token()
            while conn.execute(
                text("SELECT 1 FROM agent_referral_links WHERE token = :token"),
                {"token": token},
            ).first():
                token = gen_token()

            conn.execute(
                text(
                    """
                    INSERT INTO agent_referral_links
                        (token, agent_id, status, usage_count, is_deleted)
                    VALUES
                        (:token, :agent_id, 'ACTIVE', 0, false)
                    """
                ),
                {"token": token, "agent_id": agent_id},
            )
            created += 1
        print(f"✅ ensured referral links for agents (created {created})")


def normalize_link_status(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE agent_referral_links
                SET status = UPPER(status)
                WHERE status IN ('active','disabled','expired')
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE agents
                SET commission_mode = UPPER(commission_mode)
                WHERE commission_mode IN ('tiered','fixed_30')
                """
            )
        )
    print("✅ normalized agent_referral_links.status to uppercase values")
    print("✅ normalized agents.commission_mode to uppercase values")


def ensure_user_fk(engine: Engine) -> None:
    if not column_exists(engine, "users", "agent_referral_link_id"):
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN agent_referral_link_id INTEGER"))
        print("✅ added users.agent_referral_link_id")

    if (
        engine.dialect.name != "sqlite"
        and not fk_exists(engine, "users", "agent_referral_link_id", "agent_referral_links")
    ):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE users ADD CONSTRAINT fk_users_agent_referral_link "
                    "FOREIGN KEY (agent_referral_link_id) REFERENCES agent_referral_links(id)"
                )
            )
        print("✅ added FK for users.agent_referral_link_id")

    run_safe("CREATE INDEX ix_users_agent_referral_link_id ON users (agent_referral_link_id)")(
        engine
    )


def main() -> None:
    engine = get_engine()
    print(f"🏗  Connecting to {settings.database_url}")
    ensure_commission_mode(engine)
    normalize_link_status(engine)
    ensure_referral_links(engine)
    ensure_user_fk(engine)
    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
