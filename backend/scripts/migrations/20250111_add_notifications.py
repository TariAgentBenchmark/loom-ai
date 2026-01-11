#!/usr/bin/env python3
"""
Create notifications and user_notifications tables.
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


def main() -> None:
    engine = get_engine()

    with engine.begin() as conn:
        # Create notifications table
        if not table_exists(engine, "notifications"):
            conn.execute(
                text(
                    """
                    CREATE TABLE notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id VARCHAR(50) UNIQUE NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        type VARCHAR(20) NOT NULL DEFAULT 'system',
                        active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_notifications_id ON notifications (id)"))
            conn.execute(
                text(
                    "CREATE INDEX ix_notifications_notification_id ON notifications (notification_id)"
                )
            )
            print("✅ Created notifications table")
        else:
            print("ℹ️  notifications table already exists")

        # Create user_notifications table
        if not table_exists(engine, "user_notifications"):
            conn.execute(
                text(
                    """
                    CREATE TABLE user_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        notification_id INTEGER NOT NULL,
                        is_read BOOLEAN NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (notification_id) REFERENCES notifications (id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_user_notifications_id ON user_notifications (id)")
            )
            conn.execute(
                text(
                    "CREATE INDEX ix_user_notifications_user_id ON user_notifications (user_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX ix_user_notifications_notification_id ON user_notifications (notification_id)"
                )
            )
            print("✅ Created user_notifications table")
        else:
            print("ℹ️  user_notifications table already exists")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
