from app.services.fraud_service import assess_transaction, classify_risk, validate_amount


def test_all_rules_and_score_cap():
    result = assess_transaction(
        {"amount": 200000, "merchant_mcc": "6051"},
        {"balance": 10, "velocity_count": 8, "failed_attempt_count": 5,
         "device_history_count": 3, "unusual_device": True},
    )
    assert result.score == 100
    assert result.level == "CRITICAL"
    assert {rule.code for rule in result.rules} == {"R-VEL-01", "R-AMT-01", "R-BAL-01", "R-DEV-01", "R-REP-01", "R-MCC-01"}


def test_zero_is_low_and_none_is_unevaluated():
    assert classify_risk(0) == "LOW"
    assert classify_risk(None) == "UNEVALUATED"


def test_amount_validation():
    assert validate_amount(12.345) == 12.35

