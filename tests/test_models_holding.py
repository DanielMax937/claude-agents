"""Tests for HoldingPosition model."""
import pytest
from datetime import date as dt_date
from commodity_pipeline.models import HoldingPosition, OptionType


def test_holding_position_creation():
    """Should create a holding position with all fields."""
    position = HoldingPosition(
        code="CU2501-C-75000",
        symbol="CU",
        expiry="2025-01",
        strike=75000,
        type=OptionType.CALL,
        quantity=2,
        avg_cost=1200,
        open_date=dt_date(2024, 12, 1)
    )

    assert position.code == "CU2501-C-75000"
    assert position.symbol == "CU"
    assert position.expiry == "2025-01"
    assert position.strike == 75000
    assert position.type == OptionType.CALL
    assert position.quantity == 2
    assert position.avg_cost == 1200
    assert position.open_date == dt_date(2024, 12, 1)


def test_current_pnl_call():
    """Call P/L = (current_price - avg_cost) * quantity."""
    position = HoldingPosition(
        code="CU2501-C-75000",
        symbol="CU",
        expiry="2025-01",
        strike=75000,
        type=OptionType.CALL,
        quantity=2,
        avg_cost=1200
    )

    pnl = position.current_pnl(current_price=1450)
    assert pnl == 500  # (1450 - 1200) * 2


def test_current_pnl_put():
    """Put P/L calculation."""
    position = HoldingPosition(
        code="CU2501-P-75000",
        symbol="CU",
        expiry="2025-01",
        strike=75000,
        type=OptionType.PUT,
        quantity=1,
        avg_cost=800
    )

    pnl = position.current_pnl(current_price=1000)
    assert pnl == 200  # (1000 - 800) * 1


def test_is_itm_call():
    """Call is ITM when spot > strike."""
    position = HoldingPosition(
        code="CU2501-C-75000",
        symbol="CU",
        expiry="2025-01",
        strike=75000,
        type=OptionType.CALL,
        quantity=2,
        avg_cost=1200
    )

    assert position.is_itm(spot=75100) is True
    assert position.is_itm(spot=75000) is False  # At strike not ITM
    assert position.is_itm(spot=74900) is False


def test_is_itm_put():
    """Put is ITM when spot < strike."""
    position = HoldingPosition(
        code="CU2501-P-75000",
        symbol="CU",
        expiry="2025-01",
        strike=75000,
        type=OptionType.PUT,
        quantity=1,
        avg_cost=800
    )

    assert position.is_itm(spot=74900) is True
    assert position.is_itm(spot=75000) is False
    assert position.is_itm(spot=75100) is False


def test_days_to_expiry():
    """Should calculate days from today to expiry."""
    from datetime import datetime, timedelta

    # Create expiry date 30 days from now
    expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    position = HoldingPosition(
        code="CU2501-C-75000",
        symbol="CU",
        expiry=expiry_date,
        strike=75000,
        type=OptionType.CALL,
        quantity=2,
        avg_cost=1200
    )

    # Should return approximately 30 days (allow 1 day margin for timing)
    dte = position.days_to_expiry
    assert 28 <= dte <= 32
