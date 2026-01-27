#!/usr/bin/env python3
"""
Create task_logs table for per-task lifecycle logging.
Run manually: python backend/scripts/migrations/20260127_add_task_logs.py
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
)
from sqlalchemy.sql import func

from app.core.config import settings


def get_engine():
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False, "timeout": 20},
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


def create_task_logs_table() -> None:
    engine = get_engine()
    inspector = inspect(engine)
    if inspector.has_table("task_logs"):
        print("task_logs table already exists, skipping.")
        return

    metadata = MetaData()

    task_logs = Table(
        "task_logs",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("task_id", Integer, ForeignKey("tasks.id"), nullable=False),
        Column("task_task_id", String(50), nullable=False),
        Column("level", String(10), nullable=False, server_default="info"),
        Column("event", String(100), nullable=False),
        Column("message", Text, nullable=False),
        Column("details", JSON, nullable=True),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
        Index("ix_task_logs_task_id", "task_id"),
        Index("ix_task_logs_task_task_id", "task_task_id"),
        Index("ix_task_logs_created_at", "created_at"),
        Index("ix_task_logs_level", "level"),
        Index("ix_task_logs_event", "event"),
    )

    metadata.create_all(engine, tables=[task_logs])
    print("Created task_logs table.")


if __name__ == "__main__":
    create_task_logs_table()

