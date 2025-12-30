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


def test_ohlcv_bar_creation():
    """OHLCVBar should store OHLCV data for a single day."""
    from commodity_pipeline.models import OHLCVBar

    bar = OHLCVBar(
        date=date(2024, 12, 30),
        open=3500.0,
        high=3550.0,
        low=3480.0,
        close=3520.0,
        volume=100000
    )

    assert bar.date == date(2024, 12, 30)
    assert bar.high == 3550.0
    assert bar.volume == 100000


def test_technical_signals_creation():
    """TechnicalSignals should store all indicator results."""
    from commodity_pipeline.models import TechnicalSignals, TrendDirection

    signals = TechnicalSignals(
        commodity_code="rb2501",
        ma_signal="buy",
        macd_signal="buy",
        rsi_value=65.0,
        rsi_signal="neutral",
        boll_position="middle",
        kdj_signal="buy",
        atr_value=50.0,
        obv_trend="up",
        cci_signal="neutral",
        overall_trend=TrendDirection.BULLISH,
        strength=7
    )

    assert signals.commodity_code == "rb2501"
    assert signals.overall_trend == TrendDirection.BULLISH
    assert signals.strength == 7