"""Transaction retrieval and submission workflow."""

from datetime import datetime, timedelta
from typing import Any

from app.config import settings
from app.database import mysql_db
from app.database.mongo_db import MongoDatabase
from app.services.fraud_service import assess_transaction, validate_amount


def list_transactions(filters: dict[str, Any] | None = None, limit: int = 100) -> list[dict[str, Any]]:
    filters = filters or {}
    clauses = ["1 = 1"]
    params: list[Any] = []
    if filters.get("risk_level"):
        clauses.append("t.risk_level = %s")
        params.append(filters["risk_level"])
    if filters.get("status"):
        clauses.append("t.status = %s")
        params.append(filters["status"])
    if filters.get("merchant_id"):
        clauses.append("t.merchant_id = %s")
        params.append(filters["merchant_id"])
    if filters.get("min_amount") is not None:
        clauses.append("t.amount >= %s")
        params.append(filters["min_amount"])
    if filters.get("max_amount") is not None:
        clauses.append("t.amount <= %s")
        params.append(filters["max_amount"])
    params.append(max(1, min(int(limit), 500)))
    query = f"""SELECT t.transaction_id, t.amount, t.currency, t.transaction_type,
                       t.channel, t.location, t.transaction_timestamp, t.status,
                       t.risk_score, t.risk_level, m.merchant_name, m.mcc,
                       c.full_name AS customer_name
                FROM transactions t
                JOIN accounts a ON a.account_id = t.source_account_id
                JOIN customers c ON c.customer_id = a.customer_id
                LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
                WHERE {' AND '.join(clauses)}
                ORDER BY t.transaction_timestamp DESC LIMIT %s"""
    return mysql_db.fetch_all(query, tuple(params))


def submit_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    amount = validate_amount(float(payload["amount"]))
    with mysql_db.connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT account_id, balance, status FROM accounts WHERE account_id = %s FOR UPDATE", (payload["source_account_id"],))
            account = cur.fetchone()
            if not account or account["status"] != "ACTIVE":
                raise ValueError("Source account does not exist or is not active.")
            cur.execute("SELECT merchant_id, mcc, status FROM merchants WHERE merchant_id = %s", (payload["merchant_id"],))
            merchant = cur.fetchone()
            if not merchant or merchant["status"] != "ACTIVE":
                raise ValueError("Merchant does not exist or is not active.")
            now = datetime.utcnow()
            cur.execute(
                """SELECT COUNT(*) AS count FROM transactions
                   WHERE source_account_id = %s AND transaction_timestamp >= %s""",
                (payload["source_account_id"], now - timedelta(minutes=settings.velocity_window_minutes)),
            )
            velocity_count = int(cur.fetchone()["count"])
            cur.execute(
                """SELECT COUNT(*) AS count FROM payment_attempts
                   WHERE account_id = %s AND attempt_timestamp >= %s AND result = 'FAILED'""",
                (payload["source_account_id"], now - timedelta(minutes=settings.failed_attempt_window_minutes)),
            )
            failed_count = int(cur.fetchone()["count"])
            cur.execute(
                "SELECT COUNT(*) AS count FROM transactions WHERE source_account_id = %s AND device_id = %s",
                (payload["source_account_id"], payload["device_id"]),
            )
            device_count = int(cur.fetchone()["count"])
            assessment = assess_transaction(
                {**payload, "amount": amount, "merchant_mcc": merchant["mcc"]},
                {"balance": float(account["balance"]), "velocity_count": velocity_count,
                 "failed_attempt_count": failed_count, "device_history_count": device_count,
                 "unusual_device": device_count == 0},
            )
            cur.execute(
                """INSERT INTO transactions
                   (source_account_id, merchant_id, amount, currency, transaction_type,
                    channel, device_id, location, status, risk_score, risk_level)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (payload["source_account_id"], payload["merchant_id"], amount,
                 payload.get("currency", "INR"), payload.get("transaction_type", "PURCHASE"),
                 payload["channel"], payload["device_id"], payload.get("location"),
                 "PENDING", assessment.score, assessment.level),
            )
            transaction_id = cur.lastrowid
            if assessment.rules:
                cur.execute(
                    """INSERT INTO fraud_alerts
                       (transaction_id, score, severity, status, explanation)
                       VALUES (%s,%s,%s,'OPEN',%s)""",
                    (transaction_id, assessment.score, assessment.level,
                     " ".join(assessment.explanations)),
                )
                alert_id = cur.lastrowid
                for rule in assessment.rules:
                    cur.execute(
                        "INSERT INTO fraud_alert_rules (alert_id, rule_id) SELECT %s, rule_id FROM risk_rules WHERE rule_code = %s",
                        (alert_id, rule.code),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    try:
        MongoDatabase().record_event(transaction_id, "TRANSACTION_SUBMITTED", {
            "channel": payload["channel"], "device_id": payload["device_id"],
            "risk_score": assessment.score, "risk_level": assessment.level,
        })
    except Exception as exc:
        return {"transaction_id": transaction_id, "assessment": assessment, "telemetry_error": str(exc)}
    return {"transaction_id": transaction_id, "assessment": assessment}
