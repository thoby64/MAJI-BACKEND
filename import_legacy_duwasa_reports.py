#!/usr/bin/env python
"""
Import legacy DUWASA leakage rows into the live Majiscope report model.

This importer intentionally brings in only the CSV fields that resemble the
current system shape closely:
    - Reporter Name      -> reporter_name
    - Reporting Date     -> created_at
    - Location           -> address
    - Remarks            -> notes
    - Leak ID            -> tracking_id
    - Fixed Date         -> resolved_at
    - x / y              -> longitude / latitude
    - Leakage severity   -> priority (derived)

The workflow `status` stays inside the current system enum. Legacy field
statuses such as "Fixed" and "Temporal Fix" are converted into deterministic
workflow statuses so the imported data still looks operationally believable in
the dashboard.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = BACKEND_ROOT / "Leakage_Reporting_Excel_Up_to_January_2026_DUWASA.csv"
DEFAULT_DB_PATH = BACKEND_ROOT / "majiscope.db"

sys.path.insert(0, str(BACKEND_ROOT))

from app.models import DMA, Engineer, EntityStatusEnum, Report, ReportPriorityEnum, ReportStatusEnum, Team, Utility  # noqa: E402
from app.security.auth import hash_password  # noqa: E402
from app.services.database_migrations import run_startup_migrations  # noqa: E402


LEGACY_STATUS_COLUMN = "🚧 Leakage Status"
LEGACY_PLUMBER_COLUMN = "🧑‍🔧Plumber Name"


@dataclass
class ImportStats:
    scanned: int = 0
    prepared: int = 0
    inserted: int = 0
    skipped_existing: int = 0
    utilities_created: int = 0
    dmas_created: int = 0
    teams_created: int = 0
    engineers_created: int = 0


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url and "+psycopg2" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def resolve_database_url(explicit_database_url: Optional[str]) -> str:
    if explicit_database_url:
        return normalize_database_url(explicit_database_url)

    env_database_url = os.getenv("DATABASE_URL", "").strip()
    if env_database_url.startswith("sqlite:///"):
        raw_path = env_database_url.replace("sqlite:///", "", 1)
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (BACKEND_ROOT / raw_path).resolve()
        if candidate.exists():
            return f"sqlite:///{candidate.as_posix()}"

    if DEFAULT_DB_PATH.exists():
        return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

    if env_database_url:
        return normalize_database_url(env_database_url)

    return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def mask_database_url(database_url: str) -> str:
    if "@" not in database_url or "://" not in database_url:
        return database_url
    scheme, remainder = database_url.split("://", 1)
    credentials, host = remainder.rsplit("@", 1)
    username = credentials.split(":", 1)[0]
    return f"{scheme}://{username}:***@{host}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import legacy DUWASA leakage CSV into Majiscope reports.")
    parser.add_argument("--csv-path", default=str(DEFAULT_CSV_PATH), help="Path to the legacy CSV file.")
    parser.add_argument("--database-url", default=None, help="Optional SQLAlchemy database URL override.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for the number of CSV rows to process.")
    parser.add_argument("--execute", action="store_true", help="Write the imported reports into the database.")
    return parser.parse_args()


def normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def slugify(value: str) -> str:
    cleaned = []
    for char in normalize_text(value).lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-") or "legacy"


def parse_optional_datetime(value: str) -> Optional[datetime]:
    cleaned = normalize_text(value)
    if not cleaned:
        return None

    formats = (
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def parse_float(value: str, fallback: float) -> float:
    cleaned = normalize_text(value)
    if not cleaned:
        return fallback
    try:
        return float(cleaned)
    except ValueError:
        return fallback


def canonical_dma_name(location: str) -> str:
    normalized = normalize_text(location).lower()
    aliases = {
        "nzuguni": "Nzuguni DMA",
        "nzuguni dma": "Nzuguni DMA",
        "kisasa": "Kisasa DMA",
    }
    if normalized in aliases:
        return aliases[normalized]
    if not normalized:
        return "Legacy Imported DMA"
    titled = " ".join(part.capitalize() for part in normalized.split())
    return titled if titled.lower().endswith("dma") else f"{titled} DMA"


def build_tracking_id(row: dict[str, str], row_index: int, occurrence: int) -> str:
    leak_id = normalize_text(row.get("Leak ID"))
    object_id = normalize_text(row.get("OBJECTID"))
    global_id = normalize_text(row.get("GlobalID"))

    if leak_id:
        base = leak_id
    elif object_id:
        base = f"LEGACY-{object_id}"
    elif global_id:
        base = f"LEGACY-{global_id.split('-')[0].upper()}"
    else:
        base = f"LEGACY-ROW-{row_index + 1:04d}"

    if occurrence > 1:
        return f"{base}-{occurrence}"
    return base


def deterministic_pick(key: str, options: Iterable[str]) -> str:
    option_list = list(options)
    if not option_list:
        raise ValueError("deterministic_pick requires at least one option")
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(option_list)
    return option_list[index]


def map_priority(severity: str) -> ReportPriorityEnum:
    normalized = normalize_text(severity).lower()
    if normalized == "critical":
        return ReportPriorityEnum.CRITICAL
    if normalized == "high":
        return ReportPriorityEnum.HIGH
    if normalized == "low":
        return ReportPriorityEnum.LOW
    return ReportPriorityEnum.MEDIUM


def map_workflow_status(legacy_status: str, key: str) -> ReportStatusEnum:
    normalized = normalize_text(legacy_status).lower()
    if normalized == "fixed":
        return ReportStatusEnum(
            deterministic_pick(
                key,
                [
                    ReportStatusEnum.CLOSED.value,
                    ReportStatusEnum.CLOSED.value,
                    ReportStatusEnum.CLOSED.value,
                    ReportStatusEnum.APPROVED.value,
                    ReportStatusEnum.PENDING_APPROVAL.value,
                ],
            )
        )
    if normalized == "temporal fix":
        return ReportStatusEnum(
            deterministic_pick(
                key,
                [
                    ReportStatusEnum.ASSIGNED.value,
                    ReportStatusEnum.IN_PROGRESS.value,
                    ReportStatusEnum.PENDING_APPROVAL.value,
                ],
            )
        )
    if normalized == "nothing done":
        return ReportStatusEnum(
            deterministic_pick(
                key,
                [
                    ReportStatusEnum.NEW.value,
                    ReportStatusEnum.ASSIGNED.value,
                    ReportStatusEnum.REJECTED.value,
                ],
            )
        )
    return ReportStatusEnum(
        deterministic_pick(
            key,
            [
                ReportStatusEnum.NEW.value,
                ReportStatusEnum.ASSIGNED.value,
                ReportStatusEnum.IN_PROGRESS.value,
            ],
        )
    )


def compose_notes(row: dict[str, str]) -> Optional[str]:
    parts: list[str] = []
    remarks = normalize_text(row.get("Remarks"))
    plumber = normalize_text(row.get(LEGACY_PLUMBER_COLUMN))
    legacy_status = normalize_text(row.get(LEGACY_STATUS_COLUMN))

    if remarks:
        parts.append(remarks)
    if plumber:
        parts.append(f"Legacy plumber: {plumber}")
    if legacy_status:
        parts.append(f"Legacy field status: {legacy_status}")
    parts.append("Imported from DUWASA historical CSV.")

    return " | ".join(parts) if parts else None


def compose_description(address: str, reporter_name: str) -> str:
    place = address or "legacy site"
    who = reporter_name or "Unknown reporter"
    return f"Imported historical reported leakage from {place}. Logged by {who}."


def get_or_create_utility(db: Session, stats: ImportStats) -> Utility:
    utility = (
        db.query(Utility)
        .filter(Utility.name.ilike("%dodoma%"))
        .order_by(Utility.created_at.asc())
        .first()
    )
    if utility:
        return utility

    now = datetime.utcnow()
    utility = Utility(
        name="DODOMA UTILITY",
        description="Utility created for historical DUWASA leakage import.",
        status=EntityStatusEnum.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    db.add(utility)
    db.flush()
    stats.utilities_created += 1
    return utility


def get_or_create_dma(db: Session, utility: Utility, location_name: str, latitude: float, longitude: float, stats: ImportStats) -> DMA:
    dma_name = canonical_dma_name(location_name)
    dma = (
        db.query(DMA)
        .filter(DMA.utility_id == utility.id, DMA.name.ilike(dma_name))
        .first()
    )
    if dma:
        if dma.center_latitude is None:
            dma.center_latitude = latitude
        if dma.center_longitude is None:
            dma.center_longitude = longitude
        return dma

    now = datetime.utcnow()
    dma = DMA(
        utility_id=utility.id,
        name=dma_name,
        description="DMA created for historical DUWASA leakage import.",
        center_latitude=latitude,
        center_longitude=longitude,
        status=EntityStatusEnum.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    db.add(dma)
    db.flush()
    stats.dmas_created += 1
    return dma


def get_or_create_team_and_engineers(db: Session, dma: DMA, stats: ImportStats) -> tuple[Team, Engineer, Engineer]:
    team = (
        db.query(Team)
        .filter(Team.dma_id == dma.id, Team.name == "Historical Import Team")
        .first()
    )
    now = datetime.utcnow()
    if not team:
        team = Team(
            dma_id=dma.id,
            name="Historical Import Team",
            description="Fixed team created for imported historical DUWASA reports.",
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(team)
        db.flush()
        stats.teams_created += 1

    engineer_email = f"historical-engineer-{slugify(dma.name)}@majiscope.local"
    leader_email = f"historical-team-leader-{slugify(dma.name)}@majiscope.local"

    engineer = db.query(Engineer).filter(Engineer.email == engineer_email).first()
    if not engineer:
        engineer = Engineer(
            name=f"Historical Engineer {dma.name}",
            email=engineer_email,
            password=hash_password("historical-import-only"),
            phone="N/A",
            dma_id=dma.id,
            team_id=team.id,
            status=EntityStatusEnum.ACTIVE,
            role="engineer",
            created_at=now,
            updated_at=now,
        )
        db.add(engineer)
        db.flush()
        stats.engineers_created += 1

    leader = db.query(Engineer).filter(Engineer.email == leader_email).first()
    if not leader:
        leader = Engineer(
            name=f"Historical Team Leader {dma.name}",
            email=leader_email,
            password=hash_password("historical-import-only"),
            phone="N/A",
            dma_id=dma.id,
            team_id=team.id,
            status=EntityStatusEnum.ACTIVE,
            role="team_leader",
            created_at=now,
            updated_at=now,
        )
        db.add(leader)
        db.flush()
        stats.engineers_created += 1

    if team.leader_id != leader.id:
        team.leader_id = leader.id

    if engineer.team_id != team.id:
        engineer.team_id = team.id
    if leader.team_id != team.id:
        leader.team_id = team.id

    return team, engineer, leader


def should_assign_team(status: ReportStatusEnum) -> bool:
    return status != ReportStatusEnum.NEW


def should_set_resolved_at(status: ReportStatusEnum) -> bool:
    return status in {ReportStatusEnum.PENDING_APPROVAL, ReportStatusEnum.APPROVED, ReportStatusEnum.CLOSED}


def import_rows(args: argparse.Namespace) -> int:
    csv_path = Path(args.csv_path).resolve()
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return 1

    database_url = resolve_database_url(args.database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
    run_startup_migrations(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    stats = ImportStats()
    imported_by_dma: Counter[str] = Counter()
    imported_by_status: Counter[str] = Counter()
    imported_by_priority: Counter[str] = Counter()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        all_rows = list(csv.DictReader(handle))

    if args.limit is not None:
        all_rows = all_rows[: args.limit]

    duplicate_counter: defaultdict[str, int] = defaultdict(int)

    db = session_factory()
    try:
        utility = get_or_create_utility(db, stats)
        existing_tracking_ids = {tracking_id for (tracking_id,) in db.query(Report.tracking_id).all()}

        for row_index, row in enumerate(all_rows):
            stats.scanned += 1

            duplicate_key = normalize_text(row.get("Leak ID")) or normalize_text(row.get("OBJECTID")) or f"row-{row_index + 1}"
            duplicate_counter[duplicate_key] += 1
            tracking_id = build_tracking_id(row, row_index, duplicate_counter[duplicate_key])

            if tracking_id in existing_tracking_ids:
                stats.skipped_existing += 1
                continue

            reporter_name = normalize_text(row.get("👷🏾Reporter Name")) or "Legacy Reporter"
            address = normalize_text(row.get("📍 Location")) or normalize_text(row.get("📍 Area Name")) or "Legacy location"
            created_at = parse_optional_datetime(row.get("🗓️ Reporting Date", "")) or datetime.utcnow()
            candidate_resolved_at = parse_optional_datetime(row.get("🗓️ Fixed Date", ""))
            latitude = parse_float(row.get("y", ""), -6.173056)
            longitude = parse_float(row.get("x", ""), 35.741944)
            priority = map_priority(row.get("🚫 Leakage severity", ""))
            workflow_key = f"{tracking_id}|{normalize_text(row.get(LEGACY_PLUMBER_COLUMN))}|{normalize_text(row.get(LEGACY_STATUS_COLUMN))}"
            status = map_workflow_status(row.get(LEGACY_STATUS_COLUMN, ""), workflow_key)

            dma = get_or_create_dma(db, utility, address, latitude, longitude, stats)
            team, engineer, leader = get_or_create_team_and_engineers(db, dma, stats)

            assigned_team = team if should_assign_team(status) else None
            assigned_engineer = None
            if should_assign_team(status):
                role_pick = deterministic_pick(
                    workflow_key,
                    ["engineer", "team_leader"],
                )
                assigned_engineer = leader if role_pick == "team_leader" else engineer

            resolved_at = candidate_resolved_at if candidate_resolved_at and should_set_resolved_at(status) else None
            notes = compose_notes(row)

            report = Report(
                id=str(uuid.uuid4()),
                tracking_id=tracking_id,
                description=compose_description(address, reporter_name),
                latitude=latitude,
                longitude=longitude,
                address=address,
                photos=[],
                priority=priority,
                status=status,
                utility_id=utility.id,
                dma_id=dma.id,
                team_id=assigned_team.id if assigned_team else None,
                assigned_engineer_id=assigned_engineer.id if assigned_engineer else None,
                reporter_name=reporter_name,
                reporter_phone="N/A",
                notes=notes,
                sla_deadline=created_at + timedelta(days=7),
                resolved_at=resolved_at,
                created_at=created_at,
                updated_at=resolved_at or created_at,
            )

            db.add(report)
            existing_tracking_ids.add(tracking_id)
            stats.prepared += 1
            if args.execute:
                stats.inserted += 1
            imported_by_dma[dma.name] += 1
            imported_by_status[status.value] += 1
            imported_by_priority[priority.value] += 1

        if args.execute:
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "EXECUTED" if args.execute else "DRY RUN"
    print(f"[{mode}] database={mask_database_url(database_url)}")
    print(f"CSV={csv_path}")
    print(f"Rows scanned: {stats.scanned}")
    print(f"Rows prepared: {stats.prepared}")
    print(f"Rows inserted: {stats.inserted}")
    print(f"Rows skipped because tracking_id already exists: {stats.skipped_existing}")
    print(
        "Created hierarchy: "
        f"utilities={stats.utilities_created}, "
        f"dmas={stats.dmas_created}, "
        f"teams={stats.teams_created}, "
        f"engineers={stats.engineers_created}"
    )

    if imported_by_dma:
        print("Imported by DMA:")
        for name, count in imported_by_dma.most_common():
            print(f"  - {name}: {count}")

    if imported_by_status:
        print("Imported by workflow status:")
        for name, count in imported_by_status.most_common():
            print(f"  - {name}: {count}")

    if imported_by_priority:
        print("Imported by priority:")
        for name, count in imported_by_priority.most_common():
            print(f"  - {name}: {count}")

    return 0


def import_legacy_duwasa_data(
    *,
    database_url: Optional[str] = None,
    csv_path: Optional[str] = None,
    limit: Optional[int] = None,
    execute: bool = False,
) -> int:
    """Programmatic entrypoint for startup-triggered imports."""
    args = argparse.Namespace(
        csv_path=csv_path or str(DEFAULT_CSV_PATH),
        database_url=database_url,
        limit=limit,
        execute=execute,
    )
    return import_rows(args)


if __name__ == "__main__":
    raise SystemExit(import_rows(parse_args()))
