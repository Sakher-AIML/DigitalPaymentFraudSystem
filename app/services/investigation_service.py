"""Investigation case workflow."""

from typing import Any

from app.database import mysql_db
from app.database.mongo_db import MongoDatabase
from app.services.validation import validate_case_transition


def list_cases() -> list[dict[str, Any]]:
    return mysql_db.fetch_all(
        """SELECT ic.case_id, ic.alert_id, ic.assigned_investigator, ic.status,
                  ic.notes, ic.resolution, ic.created_at, ic.updated_at,
                  fa.transaction_id, fa.severity, fa.score
           FROM investigation_cases ic JOIN fraud_alerts fa ON fa.alert_id = ic.alert_id
           ORDER BY ic.updated_at DESC"""
    )


def create_case(alert_id: int, investigator: str, notes: str = "") -> int:
    if not investigator.strip():
        raise ValueError("An investigator name is required.")
    with mysql_db.connection() as conn:
        cur = conn.cursor()
        try:
            result = cur.callproc("sp_create_investigation_case", (alert_id, investigator.strip(), notes, 0))
            created_id = result[3]
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    try:
        MongoDatabase().record_audit("CASE_CREATED", int(created_id), {"alert_id": alert_id, "investigator": investigator})
    except Exception:
        pass
    return int(created_id)


def update_case(case_id: int, current_status: str, target_status: str, resolution: str = "", notes: str = "") -> None:
    validate_case_transition(current_status, target_status)
    if target_status == "CLOSED" and not resolution.strip():
        raise ValueError("A resolution is required before closing a case.")
    with mysql_db.connection() as conn:
        cur = conn.cursor()
        try:
            cur.callproc("sp_resolve_investigation_case", (case_id, target_status, resolution, notes))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    try:
        MongoDatabase().record_audit("CASE_UPDATED", case_id, {"status": target_status, "resolution": resolution})
    except Exception:
        pass
