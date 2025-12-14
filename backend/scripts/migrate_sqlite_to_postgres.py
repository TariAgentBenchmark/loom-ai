#!/usr/bin/env python3
"""
Copy data from a SQLite database into a PostgreSQL database.

Usage:
    python scripts/migrate_sqlite_to_postgres.py \
        --sqlite-url sqlite:///./data/loom_ai.db \
        --postgres-url postgresql+psycopg://user:pass@host:5432/dbname

The script will:
1) Create all tables in the target Postgres database (using SQLAlchemy models).
2) Optionally clear existing data in Postgres before import.
3) Copy rows table by table in dependency order.
4) Reset Postgres sequences for integer primary keys.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List, Mapping

from sqlalchemy import Integer, create_engine, select, func, text, inspect
from sqlalchemy.engine import Engine

from app.core.database import Base, settings


def chunked(iterable: Iterable[Mapping], size: int) -> Iterable[List[Mapping]]:
    """Yield chunks from iterable."""
    chunk: List[Mapping] = []
    for item in iterable:
        mapping = getattr(item, "_mapping", None)
        chunk.append(dict(mapping if mapping is not None else item))
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def validate_urls(sqlite_url: str, postgres_url: str) -> None:
    if not sqlite_url.startswith("sqlite"):
        raise ValueError("sqlite-url must point to a SQLite database.")
    if not postgres_url.startswith(("postgresql", "postgres")):
        raise ValueError("postgres-url must point to a PostgreSQL database.")


def create_tables(pg_engine: Engine) -> None:
    Base.metadata.create_all(bind=pg_engine)


def truncate_tables(pg_engine: Engine) -> None:
    with pg_engine.begin() as conn:
        conn.execute(text("SET session_replication_role = 'replica'"))
        try:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
        finally:
            conn.execute(text("SET session_replication_role = 'origin'"))


def copy_table_data(
    sqlite_engine: Engine,
    pg_engine: Engine,
    batch_size: int,
) -> None:
    tables = list(Base.metadata.sorted_tables)
    if not tables:
        raise RuntimeError(
            "No SQLAlchemy models registered. Ensure app.models is imported before running the migration."
        )

    src_conn = sqlite_engine.connect()
    tgt_conn = pg_engine.connect()
    inspector = inspect(sqlite_engine)

    trans = tgt_conn.begin()
    tgt_conn.execute(text("SET session_replication_role = 'replica'"))

    try:
        for table in tables:
            # Only copy columns that exist in the SQLite source to avoid missing-column errors.
            src_columns = {col["name"] for col in inspector.get_columns(table.name)}
            if not src_columns:
                print(f"⚠️  Skipping {table.name}: table not found in SQLite source")
                continue

            columns_to_copy = [col for col in table.columns if col.name in src_columns]
            if not columns_to_copy:
                print(f"⚠️  Skipping {table.name}: no shared columns between SQLite and models")
                continue

            result = src_conn.execute(select(*columns_to_copy).select_from(table))
            total = 0
            for rows in chunked(result, batch_size):
                tgt_conn.execute(table.insert(), rows)
                total += len(rows)
            print(f"✅ Copied {total:>6} rows -> {table.name}")

        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        tgt_conn.execute(text("SET session_replication_role = 'origin'"))
        src_conn.close()
        tgt_conn.close()


def reset_sequences(pg_engine: Engine) -> None:
    with pg_engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            pk_cols = [c for c in table.columns if c.primary_key]
            if len(pk_cols) != 1:
                continue
            pk_col = pk_cols[0]
            if not isinstance(pk_col.type, Integer):
                continue

            max_id = conn.execute(select(func.max(pk_col))).scalar() or 0
            # setval requires value >= 1; use 1 when table is empty.
            setval_value = max_id if max_id > 0 else 1
            seq_sql = text(
                "SELECT setval(pg_get_serial_sequence(:table_name, :pk), :value, true)"
            )
            conn.execute(
                seq_sql,
                {
                    "table_name": table.name,
                    "pk": pk_col.name,
                    "value": setval_value,
                },
            )
            print(f"🔄 Reset sequence for {table.name}.{pk_col.name} to {setval_value}")


def main(argv: list[str] | None = None) -> None:
    # Ensure SQLAlchemy models are registered on Base.metadata
    try:
        import app.models  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "Failed to import app.models. Make sure the project root (backend/) is on PYTHONPATH."
        ) from exc

    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to PostgreSQL."
    )
    parser.add_argument(
        "--sqlite-url",
        default=settings.database_url,
        help="Source SQLite URL (default: current DATABASE_URL setting)",
    )
    parser.add_argument(
        "--postgres-url",
        required=True,
        help="Target PostgreSQL URL (postgresql+psycopg://user:pass@host:port/db)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of rows to insert per batch (default: 500)",
    )
    parser.add_argument(
        "--wipe-target",
        action="store_true",
        help="Truncate all target tables before import.",
    )
    args = parser.parse_args(argv)

    validate_urls(args.sqlite_url, args.postgres_url)

    sqlite_engine = create_engine(
        args.sqlite_url,
        connect_args={"check_same_thread": False, "timeout": 20},
    )
    pg_engine = create_engine(args.postgres_url, pool_pre_ping=True)

    print("⚙️  Ensuring tables exist in target Postgres...")
    create_tables(pg_engine)

    if args.wipe_target:
        print("🧹 Truncating existing data in target...")
        truncate_tables(pg_engine)

    print("🚚 Copying data from SQLite to Postgres...")
    copy_table_data(sqlite_engine, pg_engine, batch_size=args.batch_size)

    print("🔧 Resetting sequences...")
    reset_sequences(pg_engine)

    print("🎉 Migration complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"❌ Migration failed: {exc}")
        sys.exit(1)
