#!/usr/bin/env python3
"""
Add user referral support to the existing database.

Usage:
    uv run python scripts/migrations/20260415_add_user_referrals.py
    # or
    python scripts/migrations/20260415_add_user_referrals.py
"""

from __future__ import annotations

import secrets
import string
import sys
from typing import Callable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings


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
            pass

    return runner


def ensure_user_column(
    engine: Engine,
    column_name: str,
    ddl: str,
    fk_stmt: str | None = None,
    fk_target_table: str | None = None,
    index_stmt: str | None = None,
) -> None:
    """Add a column/index (and FK on non-SQLite) if missing."""
    if column_exists(engine, "users", column_name):
        print(f"ℹ️  users.{column_name} already present")
    else:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {ddl}"))
        print(f"✅ added users.{column_name}")

    if (
        fk_stmt
        and fk_target_table
        and engine.dialect.name != "sqlite"
        and not fk_exists(engine, "users", column_name, fk_target_table)
    ):
        with engine.begin() as conn:
            conn.execute(text(fk_stmt))
        print(f"✅ added FK for users.{column_name}")

    if index_stmt:
        run_safe(index_stmt)(engine)


def _generate_referral_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def backfill_referral_codes(engine: Engine) -> None:
    """Generate referral codes for existing users that do not have one."""
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE referral_code IS NULL OR referral_code = ''
                """
            )
        ).fetchall()
        if not rows:
            print("ℹ️  no users need referral code backfill")
            return

        created = 0
        for (user_id,) in rows:
            code = _generate_referral_code()
            while conn.execute(
                text("SELECT 1 FROM users WHERE referral_code = :code"),
                {"code": code},
            ).first():
                code = _generate_referral_code()

            conn.execute(
                text("UPDATE users SET referral_code = :code WHERE id = :user_id"),
                {"code": code, "user_id": user_id},
            )
            created += 1

        print(f"✅ backfilled {created} user referral code(s)")


def main() -> None:
    engine = get_engine()
    print(f"🏗  Connecting to {settings.database_url}")

    ensure_user_column(
        engine=engine,
        column_name="referral_code",
        ddl="referral_code VARCHAR(16)",
        index_stmt="CREATE UNIQUE INDEX ux_users_referral_code ON users (referral_code)",
    )
    ensure_user_column(
        engine=engine,
        column_name="referrer_user_id",
        ddl="referrer_user_id INTEGER",
        fk_stmt="ALTER TABLE users ADD CONSTRAINT fk_users_referrer_user FOREIGN KEY (referrer_user_id) REFERENCES users(id)",
        fk_target_table="users",
        index_stmt="CREATE INDEX ix_users_referrer_user_id ON users (referrer_user_id)",
    )
    ensure_user_column(
        engine=engine,
        column_name="referral_source",
        ddl="referral_source VARCHAR(20)",
    )

    backfill_referral_codes(engine)
    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
