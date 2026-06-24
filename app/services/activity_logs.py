"""
Activity log helpers for auditable workflow events.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import ActivityLog, Report


def create_activity_log(
    db: Session,
    *,
    action: str,
    user_name: str,
    user_role: str,
    entity: str,
    entity_id: str,
    details: Optional[str] = None,
    user_id: Optional[str] = None,
    utility_mgr_id: Optional[str] = None,
    dma_mgr_id: Optional[str] = None,
    engineer_id: Optional[str] = None,
    utility_id: Optional[str] = None,
    dma_id: Optional[str] = None,
    flush: bool = True,
) -> ActivityLog:
    log = ActivityLog(
        action=action,
        user_id=user_id,
        utility_mgr_id=utility_mgr_id,
        dma_mgr_id=dma_mgr_id,
        engineer_id=engineer_id,
        user_name=user_name,
        user_role=user_role,
        entity=entity,
        entity_id=entity_id,
        details=details,
        utility_id=utility_id,
        dma_id=dma_id,
    )
    db.add(log)
    if flush:
        db.flush()
    return log


def log_report_activity(
    db: Session,
    *,
    report: Report,
    action: str,
    details: Optional[str],
    actor: Optional[Any] = None,
    actor_name: Optional[str] = None,
    actor_role: Optional[str] = None,
    flush: bool = True,
) -> ActivityLog:
    user_id = None
    utility_mgr_id = None
    dma_mgr_id = None
    engineer_id = None

    inferred_name = actor_name or "System"
    inferred_role = actor_role or "system"

    if actor is not None:
        inferred_name = getattr(actor, "name", None) or inferred_name
        inferred_role = (
            getattr(actor, "role", None)
            or getattr(actor, "user_type", None)
            or inferred_role
        )
        actor_type = getattr(actor, "user_type", None)
        actor_id = getattr(actor, "id", None)

        if actor_type == "user":
            user_id = actor_id
        elif actor_type == "utility_manager":
            utility_mgr_id = actor_id
        elif actor_type == "dma_manager":
            dma_mgr_id = actor_id
        elif actor_type in {"engineer", "team_leader"}:
            engineer_id = actor_id

    return create_activity_log(
        db,
        action=action,
        user_name=inferred_name,
        user_role=str(inferred_role),
        entity="report",
        entity_id=report.id,
        details=details,
        user_id=user_id,
        utility_mgr_id=utility_mgr_id,
        dma_mgr_id=dma_mgr_id,
        engineer_id=engineer_id,
        utility_id=report.utility_id,
        dma_id=report.dma_id,
        flush=flush,
    )
