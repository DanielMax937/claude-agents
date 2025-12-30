"""Tests for data models."""
import pytest
from datetime import date


def test_trend_direction_enum_values():
    """TrendDirection enum should have bullish, bearish, neutral values."""
    from commodity_pipeline.models import TrendDirection

    assert TrendDirection.BULLISH.value == "bullish"
    assert TrendDirection.BEARISH.value == "bearish"
    assert TrendDirection.NEUTRAL.value == "neutral"


def test_commodity_dataclass_creation():
    """Commodity dataclass should be creatable with required fields."""
    from commodity_pipeline.models import Commodity

    c = Commodity(
        code="rb2501",
        name="螺纹钢",
        exchange="SHFE",
        main_contract="rb2501",
        price=3500.0,
        change_1d=1.5,
        change_3d=2.3,
        change_5d=-0.8
    )

    assert c.code == "rb2501"
    assert c.name == "螺纹钢"
    assert c.price == 3500.0
    assert c.change_1d == 1.5
