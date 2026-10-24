import pytest

from app.services.validation import parse_amount, validate_case_transition


def test_invalid_amounts():
    with pytest.raises(ValueError):
        parse_amount(0)
    with pytest.raises(ValueError):
        parse_amount("not-a-number")


def test_case_transitions():
    validate_case_transition("OPEN", "IN_REVIEW")
    with pytest.raises(ValueError):
        validate_case_transition("CLOSED", "OPEN")

