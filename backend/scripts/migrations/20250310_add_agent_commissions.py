#!/usr/bin/env python3
"""
Add agent_commissions table.
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
    if table_exists(engine, "agent_commissions"):
        print("ℹ️  agent_commissions already exists")
        return

    stmt = """
    CREATE TABLE agent_commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        rate NUMERIC(5,4) NOT NULL,
        status VARCHAR(20) DEFAULT 'unsettled',
        paid_at DATETIME NULL,
        settled_at DATETIME NULL,
        settled_by INTEGER NULL,
        notes VARCHAR(255) NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))
        conn.execute(text("CREATE INDEX ix_agent_commissions_agent_id ON agent_commissions (agent_id)"))
        conn.execute(text("CREATE INDEX ix_agent_commissions_order_id ON agent_commissions (order_id)"))
        conn.execute(text("CREATE INDEX ix_agent_commissions_status ON agent_commissions (status)"))
    print("✅ Created agent_commissions table")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
