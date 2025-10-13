#!/usr/bin/env python3
"""
Utility migration to ensure the users.email column allows NULL values.

Background:
Existing installations that predate the switch to phone-first registration
may still carry a NOT NULL constraint on the `email` column. When users try
to register with only a phone number this constraint causes SQLite to raise
`IntegrityError: NOT NULL constraint failed: users.email`.

Running this script will:
1. Inspect the current `users` table definition.
2. When the `email` column is still NOT NULL, recreate the table with the
   expected schema (email nullable, phone enforced as NOT NULL).
3. Copy all existing user records into the new table and rebuild indexes.

The script is idempotent – if the column is already nullable no changes are
made.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager

from sqlalchemy import text

# Ensure the backend package is importable when executed directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import engine  # noqa: E402


@contextmanager
def transactional_connection():
    """Yield a connection with autocommit disabled and commit/rollback safety."""
    conn = engine.connect()
    trans = conn.begin()
    try:
        yield conn
    except Exception:
        trans.rollback()
        conn.close()
        raise
    else:
        trans.commit()
        conn.close()


def email_column_is_nullable(conn) -> bool:
    """Return True when the users.email column already allows NULL values."""
    pragma = conn.execute(text("PRAGMA table_info(users)")).fetchall()
    for column in pragma:
        # column tuple: (cid, name, type, notnull, dflt_value, pk)
        if column[1] == "email":
            return column[3] == 0  # notnull == 0 means nullable
    raise RuntimeError("users table does not contain an email column")


def recreate_users_table_with_nullable_email(conn) -> None:
    """Rebuild the users table so email is nullable and phone is required."""
    # Disable FK checks while recreating the table
    conn.exec_driver_sql("PRAGMA foreign_keys=OFF;")
    try:
        conn.exec_driver_sql("DROP TABLE IF EXISTS users_temp;")
        conn.exec_driver_sql(
            """
            CREATE TABLE users_temp (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                email VARCHAR(255),
                hashed_password VARCHAR(255) NOT NULL,
                nickname VARCHAR(100),
                phone VARCHAR(20) NOT NULL,
                avatar_url VARCHAR(500),
                credits INTEGER,
                total_processed INTEGER,
                monthly_processed INTEGER,
                membership_type VARCHAR(10),
                membership_expiry DATETIME,
                status VARCHAR(9),
                is_email_verified BOOLEAN,
                email_verification_token VARCHAR(255),
                reset_token VARCHAR(255),
                reset_token_expires DATETIME,
                notification_settings TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login_at DATETIME,
                scheduled_deletion DATETIME,
                deletion_reason VARCHAR(500),
                is_admin BOOLEAN DEFAULT 0,
                phone_verification_code VARCHAR(10),
                phone_verification_expires TIMESTAMP,
                is_phone_verified BOOLEAN DEFAULT FALSE,
                phone_verified_at TIMESTAMP,
                last_sms_sent TIMESTAMP,
                sms_attempts_today INTEGER DEFAULT 0
            );
            """
        )

        conn.exec_driver_sql(
            """
            INSERT INTO users_temp (
                id,
                user_id,
                email,
                hashed_password,
                nickname,
                phone,
                avatar_url,
                credits,
                total_processed,
                monthly_processed,
                membership_type,
                membership_expiry,
                status,
                is_email_verified,
                email_verification_token,
                reset_token,
                reset_token_expires,
                notification_settings,
                created_at,
                updated_at,
                last_login_at,
                scheduled_deletion,
                deletion_reason,
                is_admin,
                phone_verification_code,
                phone_verification_expires,
                is_phone_verified,
                phone_verified_at,
                last_sms_sent,
                sms_attempts_today
            )
            SELECT
                id,
                user_id,
                email,
                hashed_password,
                nickname,
                COALESCE(phone, 'TMP' || printf('%010d', id)),
                avatar_url,
                credits,
                total_processed,
                monthly_processed,
                membership_type,
                membership_expiry,
                status,
                is_email_verified,
                email_verification_token,
                reset_token,
                reset_token_expires,
                notification_settings,
                created_at,
                updated_at,
                last_login_at,
                scheduled_deletion,
                deletion_reason,
                is_admin,
                phone_verification_code,
                phone_verification_expires,
                is_phone_verified,
                phone_verified_at,
                last_sms_sent,
                sms_attempts_today
            FROM users;
            """
        )

        conn.exec_driver_sql("DROP TABLE users;")
        conn.exec_driver_sql("ALTER TABLE users_temp RENAME TO users;")

        # Re-create indexes dropped with the old table
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_user_id ON users (user_id);"
        )
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);"
        )
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users (phone);"
        )
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);")
    finally:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON;")


def main() -> None:
    with transactional_connection() as conn:
        if email_column_is_nullable(conn):
            print("users.email is already nullable; no changes applied.")
            return

        print("Updating users table to allow NULL email values...")
        existing_null_phones = conn.execute(
            text("SELECT COUNT(1) FROM users WHERE phone IS NULL")
        ).scalar_one()
        if existing_null_phones:
            raise RuntimeError(
                "Cannot enforce NOT NULL on phone column because NULL values exist."
            )

        recreate_users_table_with_nullable_email(conn)
        print("users.email column successfully updated to be nullable.")


if __name__ == "__main__":
    main()
