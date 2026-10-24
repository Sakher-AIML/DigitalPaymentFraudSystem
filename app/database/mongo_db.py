"""MongoDB telemetry and audit-log adapter."""

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient

from app.config import settings


class MongoDatabase:
    def __init__(self) -> None:
        self.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2500)
        self.database = self.client[settings.mongo_database]
        self.events = self.database["transaction_events"]
        self.audit_logs = self.database["investigation_audit_logs"]

    def ping(self) -> None:
        self.client.admin.command("ping")

    def ensure_indexes(self) -> None:
        self.events.create_index([("transaction_id", ASCENDING)])
        self.events.create_index([("event_type", ASCENDING), ("created_at", DESCENDING)])
        self.audit_logs.create_index([("case_id", ASCENDING), ("created_at", DESCENDING)])

    def record_event(self, transaction_id: int, event_type: str, details: dict[str, Any]) -> str:
        result = self.events.insert_one({
            "transaction_id": transaction_id,
            "event_type": event_type,
            "details": details,
            "created_at": datetime.now(timezone.utc),
        })
        return str(result.inserted_id)

    def record_audit(self, action: str, case_id: int, details: dict[str, Any]) -> str:
        result = self.audit_logs.insert_one({
            "case_id": case_id,
            "action": action,
            "details": details,
            "created_at": datetime.now(timezone.utc),
        })
        return str(result.inserted_id)

    def transaction_events(self, transaction_id: int) -> list[dict[str, Any]]:
        return list(self.events.find({"transaction_id": transaction_id}).sort("created_at", DESCENDING))

    def case_audit_logs(self, case_id: int) -> list[dict[str, Any]]:
        return list(self.audit_logs.find({"case_id": case_id}).sort("created_at", DESCENDING))
