"""Environment-backed application configuration."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "digital_payment_fraud")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    mongo_database: str = os.getenv("MONGO_DATABASE", "digital_payment_telemetry")
    max_transaction_amount: float = float(os.getenv("MAX_TRANSACTION_AMOUNT", "1000000"))
    velocity_window_minutes: int = int(os.getenv("VELOCITY_WINDOW_MINUTES", "10"))
    velocity_limit: int = int(os.getenv("VELOCITY_LIMIT", "5"))
    high_value_threshold: float = float(os.getenv("HIGH_VALUE_THRESHOLD", "50000"))
    failed_attempt_window_minutes: int = int(os.getenv("FAILED_ATTEMPT_WINDOW_MINUTES", "30"))
    failed_attempt_limit: int = int(os.getenv("FAILED_ATTEMPT_LIMIT", "3"))
    unusual_device_min_history: int = int(os.getenv("UNUSUAL_DEVICE_MIN_HISTORY", "2"))
    high_risk_mcc: tuple[str, ...] = tuple(
        item.strip() for item in os.getenv("HIGH_RISK_MCC", "7995,4829,6051").split(",") if item.strip()
    )
    medium_threshold: int = int(os.getenv("MEDIUM_RISK_THRESHOLD", "25"))
    high_threshold: int = int(os.getenv("HIGH_RISK_THRESHOLD", "50"))
    critical_threshold: int = int(os.getenv("CRITICAL_RISK_THRESHOLD", "80"))

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def mysql_config(self) -> dict[str, object]:
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
        }


settings = Settings()
