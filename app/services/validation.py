"""Input and workflow validation."""

from decimal import Decimal

ALLOWED_CASE_TRANSITIONS = {
    "OPEN": {"IN_REVIEW", "CLOSED"},
    "IN_REVIEW": {"CLOSED", "OPEN"},
    "CLOSED": set(),
}


def parse_amount(value: object) -> float:
    try:
        amount = float(Decimal(str(value)))
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError("Enter a valid numeric amount.") from exc
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(amount, 2)


def validate_case_transition(current: str, target: str) -> None:
    if target not in ALLOWED_CASE_TRANSITIONS.get(current, set()):
        raise ValueError(f"Cannot change a {current} case to {target}.")
