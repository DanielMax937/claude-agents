"""Tests for option code parser."""
import pytest
from commodity_pipeline.utils.parsers import parse_option_code, parse_holdings


def test_parse_call_code():
    """Should parse standard call option code."""
    result = parse_option_code("CU2501-C-75000")

    assert result["symbol"] == "CU"
    assert result["expiry"] == "2025-01"
    assert result["strike"] == 75000.0
    assert result["type"] == "call"
    assert result["raw_code"] == "CU2501-C-75000"


def test_parse_put_code():
    """Should parse standard put option code."""
    result = parse_option_code("CU2501-P-73000")

    assert result["symbol"] == "CU"
    assert result["expiry"] == "2025-01"
    assert result["strike"] == 73000.0
    assert result["type"] == "put"


def test_parse_lower_case_type():
    """Should handle lowercase type suffix."""
    result = parse_option_code("rb2505-c-3500")

    assert result["symbol"] == "RB"
    assert result["type"] == "call"


def test_parse_with_m_suffix():
    """Should handle options with month suffix."""
    result = parse_option_code("CU2501M-C-75000")

    assert result["symbol"] == "CU"
    assert result["expiry"] == "2025-01"


def test_parse_invalid_format_raises():
    """Should raise ValueError for invalid format."""
    with pytest.raises(ValueError, match="Invalid option code format"):
        parse_option_code("INVALID")


def test_parse_holdings_list():
    """Should parse a list of holding dicts and enrich with parsed data."""
    holdings = [
        {"code": "CU2501-C-75000", "quantity": 2, "avg_cost": 1200},
        {"code": "CU2501-P-73000", "quantity": 1, "avg_cost": 800},
    ]

    result = parse_holdings(holdings)

    assert len(result) == 2
    assert result[0]["symbol"] == "CU"
    assert result[0]["strike"] == 75000.0
    assert result[0]["type"] == "call"
    assert result[1]["type"] == "put"
