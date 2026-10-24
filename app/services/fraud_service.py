"""Explainable, deterministic fraud scoring rules."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import settings


@dataclass(frozen=True)
class RuleResult:
    code: str
    points: int
    reason: str


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    level: str
    rules: tuple[RuleResult, ...]

    @property
    def explanations(self) -> list[str]:
        return [rule.reason for rule in self.rules]


def classify_risk(score: int | None) -> str:
    if score is None:
        return "UNEVALUATED"
    if score >= settings.critical_threshold:
        return "CRITICAL"
    if score >= settings.high_threshold:
        return "HIGH"
    if score >= settings.medium_threshold:
        return "MEDIUM"
    return "LOW"


def validate_amount(amount: float) -> float:
    if amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")
    if amount > settings.max_transaction_amount:
        raise ValueError(f"Transaction amount cannot exceed {settings.max_transaction_amount:,.2f}.")
    return round(float(amount), 2)


def assess_transaction(transaction: dict[str, Any], context: dict[str, Any]) -> RiskAssessment:
    rules: list[RuleResult] = []
    amount = float(transaction["amount"])
    balance = context.get("balance")
    if context.get("velocity_count", 0) >= settings.velocity_limit:
        rules.append(RuleResult("R-VEL-01", 20, f"{context['velocity_count']} transactions occurred within {settings.velocity_window_minutes} minutes."))
    if amount > settings.high_value_threshold:
        rules.append(RuleResult("R-AMT-01", 25, f"Amount exceeds the configured threshold of {settings.high_value_threshold:,.2f}."))
    if balance is not None and balance < amount:
        rules.append(RuleResult("R-BAL-01", 35, "Available account balance is lower than the requested amount."))
    if context.get("unusual_device") and context.get("device_history_count", 0) >= settings.unusual_device_min_history:
        rules.append(RuleResult("R-DEV-01", 15, "The device is unusual compared with this account's prior device history."))
    if context.get("failed_attempt_count", 0) >= settings.failed_attempt_limit:
        rules.append(RuleResult("R-REP-01", 20, f"{context['failed_attempt_count']} failed attempts occurred within {settings.failed_attempt_window_minutes} minutes."))
    if str(transaction.get("merchant_mcc", "")) in settings.high_risk_mcc:
        rules.append(RuleResult("R-MCC-01", 20, "The merchant category is configured as high risk for review."))
    unique_rules = {rule.code: rule for rule in rules}
    score = min(100, sum(rule.points for rule in unique_rules.values()))
    return RiskAssessment(score=score, level=classify_risk(score), rules=tuple(unique_rules.values()))
