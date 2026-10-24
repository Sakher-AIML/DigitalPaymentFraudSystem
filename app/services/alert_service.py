"""Fraud-alert retrieval and updates."""

from typing import Any

from app.database import mysql_db


def list_alerts(severity: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    clauses = ["1 = 1"]
    params: list[Any] = []
    if severity:
        clauses.append("fa.severity = %s")
        params.append(severity)
    if status:
        clauses.append("fa.status = %s")
        params.append(status)
    return mysql_db.fetch_all(
        f"""SELECT fa.alert_id, fa.transaction_id, fa.score, fa.severity, fa.status,
                   fa.explanation, fa.created_at, GROUP_CONCAT(rr.rule_code) AS rules
            FROM fraud_alerts fa
            LEFT JOIN fraud_alert_rules far ON far.alert_id = fa.alert_id
            LEFT JOIN risk_rules rr ON rr.rule_id = far.rule_id
            WHERE {' AND '.join(clauses)}
            GROUP BY fa.alert_id ORDER BY fa.created_at DESC""",
        tuple(params),
    )


def update_alert_status(alert_id: int, status: str) -> None:
    if status not in {"OPEN", "ACKNOWLEDGED", "RESOLVED", "FALSE_POSITIVE"}:
        raise ValueError("Invalid alert status.")
    with mysql_db.connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("UPDATE fraud_alerts SET status = %s WHERE alert_id = %s", (status, alert_id))
            if cur.rowcount != 1:
                raise ValueError("Alert was not found.")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
