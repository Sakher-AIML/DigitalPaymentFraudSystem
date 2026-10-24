"""Check required MySQL and MongoDB connectivity without exposing credentials."""

from app.database import mysql_db
from app.database.mongo_db import MongoDatabase


def main() -> int:
    checks = [
        ("MySQL connection", lambda: mysql_db.fetch_one("SELECT 1")),
        ("MySQL schema", lambda: mysql_db.fetch_one("SELECT COUNT(*) AS count FROM risk_rules")),
        ("MongoDB connection", lambda: MongoDatabase().ping()),
    ]
    failed = 0
    for label, check in checks:
        try:
            check()
            print(f"[OK] {label}")
        except Exception as exc:
            failed += 1
            print(f"[ERROR] {label}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
