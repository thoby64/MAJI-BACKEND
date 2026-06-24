#!/usr/bin/env python
"""
Migrate the local Majiscope SQLite database into a PostgreSQL database.

Usage:
    python migrate_sqlite_to_postgres.py --source ./majiscope.db --target <postgres-url> --replace
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, create_engine, delete, insert, select, update
from sqlalchemy.engine import Engine

from app.database.session import _normalize_database_url
from app.models import Base


TABLE_ORDER = [
    "user",
    "utility",
    "utility_manager",
    "dma",
    "dma_manager",
    "team",
    "engineer",
    "report",
    "image_upload",
    "notification",
    "push_device_token",
    "activity_log",
]


def _create_sqlite_engine(source: Path) -> Engine:
    return create_engine(f"sqlite:///{source}")


def _create_postgres_engine(target_url: str) -> Engine:
    return create_engine(_normalize_database_url(target_url), pool_pre_ping=True)


def _reflect(engine: Engine) -> MetaData:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return metadata


def _table_counts(engine: Engine, metadata: MetaData) -> dict[str, int]:
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        for table_name in TABLE_ORDER:
            table = metadata.tables[table_name]
            counts[table_name] = conn.execute(select(table)).fetchall().__len__()
    return counts


def _fetch_rows(engine: Engine, metadata: MetaData, table_name: str) -> list[dict[str, Any]]:
    table = metadata.tables[table_name]
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(select(table)).mappings().all()]


def _clear_target(engine: Engine, metadata: MetaData) -> None:
    with engine.begin() as conn:
        for table_name in reversed(TABLE_ORDER):
            conn.execute(delete(metadata.tables[table_name]))


def _insert_rows(engine: Engine, metadata: MetaData, table_name: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    table = metadata.tables[table_name]
    with engine.begin() as conn:
        conn.execute(insert(table), rows)


def _migrate(source: Path, target_url: str, replace: bool) -> None:
    source_engine = _create_sqlite_engine(source)
    target_engine = _create_postgres_engine(target_url)

    # Ensure the target schema exists.
    Base.metadata.create_all(bind=target_engine)

    source_meta = _reflect(source_engine)
    target_meta = _reflect(target_engine)

    missing_tables = [name for name in TABLE_ORDER if name not in source_meta.tables]
    if missing_tables:
        raise RuntimeError(f"Source database is missing expected tables: {missing_tables}")

    source_counts = _table_counts(source_engine, source_meta)
    print("Source counts:")
    for table_name in TABLE_ORDER:
        print(f"  {table_name}: {source_counts[table_name]}")

    if replace:
        print("\nClearing target tables before import...")
        _clear_target(target_engine, target_meta)

    buffered_rows = {name: _fetch_rows(source_engine, source_meta, name) for name in TABLE_ORDER}

    # Break the team/engineer circular reference during insert.
    team_leaders = {row["id"]: row.get("leader_id") for row in buffered_rows["team"]}
    for row in buffered_rows["team"]:
        row["leader_id"] = None

    print("\nCopying rows to PostgreSQL...")
    for table_name in TABLE_ORDER:
        _insert_rows(target_engine, target_meta, table_name, buffered_rows[table_name])
        print(f"  inserted {len(buffered_rows[table_name])} rows into {table_name}")

    # Restore team leaders after engineers exist.
    team_table = target_meta.tables["team"]
    with target_engine.begin() as conn:
        for team_id, leader_id in team_leaders.items():
            if leader_id:
                conn.execute(
                    update(team_table)
                    .where(team_table.c.id == team_id)
                    .values(leader_id=leader_id)
                )

    target_counts = _table_counts(target_engine, target_meta)
    print("\nTarget counts:")
    for table_name in TABLE_ORDER:
        print(f"  {table_name}: {target_counts[table_name]}")

    print("\nMigration completed successfully.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Majiscope SQLite data to PostgreSQL.")
    parser.add_argument("--source", required=True, help="Path to the SQLite database file.")
    parser.add_argument("--target", required=True, help="PostgreSQL database URL.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Clear existing PostgreSQL data before importing.",
    )
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not source.exists():
        raise FileNotFoundError(f"SQLite source database not found: {source}")

    _migrate(source, args.target, args.replace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
