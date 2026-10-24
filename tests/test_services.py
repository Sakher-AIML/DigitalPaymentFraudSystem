from unittest.mock import patch

import pytest

from app.services.transaction_service import list_transactions


def test_transaction_query_uses_parameterized_filters():
    with patch("app.services.transaction_service.mysql_db.fetch_all", return_value=[]) as fetch:
        assert list_transactions({"risk_level": "HIGH", "status": "PENDING"}, 20) == []
        query, params = fetch.call_args.args
        assert "%s" in query
        assert params[:2] == ("HIGH", "PENDING")


def test_missing_database_errors_are_not_success():
    with patch("app.services.transaction_service.mysql_db.fetch_all", side_effect=RuntimeError("offline")):
        with pytest.raises(RuntimeError):
            list_transactions()
