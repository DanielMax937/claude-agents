"""Tests for Terminal output formatter."""
import pytest
from datetime import date
from io import StringIO


def test_terminal_output_format_commodity_summary():
    """format_commodity_summary should output colored terminal text."""
    from commodity_pipeline.output.terminal import TerminalOutput
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )

    output = TerminalOutput(use_colors=False)  # Disable colors for testing

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)

    technical = TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )

    options = [
        OptionContract(
            "rb2501C3500", "rb2501", 3500.0, date(2025, 1, 15), "call",
            50.0, 1000, 0.25, 0.55, 0.02, -5.0, 10.0, 0.5, 48.0, 2.0
        )
    ]

    news = [NewsItem("价格上涨", "eastmoney", "http://1", date.today())]

    strategies = [
        StrategyRecommendation(
            "Long Call", "directional",
            [{"action": "buy", "option": "rb2501C3500"}],
            float("inf"), 50.0, [3550.0],
            "Bullish momentum", 7
        )
    ]

    result = output.format_commodity_summary(
        commodity, technical, options, news, strategies
    )

    # Should contain key information
    assert "rb2501" in result
    assert "螺纹钢" in result
    assert "3500" in result
    assert "BULLISH" in result or "bullish" in result.lower()
    assert "Long Call" in result


def test_terminal_output_format_all():
    """format_all should create complete terminal report."""
    from commodity_pipeline.output.terminal import TerminalOutput
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )

    output = TerminalOutput(use_colors=False)

    commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
    ]

    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    options = {"rb2501": []}
    news = {"rb2501": []}
    strategies = {"rb2501": []}
    alerts = []

    result = output.format_all(commodities, technical, options, news, strategies, alerts)

    assert "rb2501" in result
    assert "螺纹钢" in result


def test_terminal_output_trend_colors():
    """Trend direction should use appropriate colors."""
    from commodity_pipeline.output.terminal import TerminalOutput

    output = TerminalOutput(use_colors=True)

    # Check color methods exist and return strings
    assert isinstance(output._trend_color(True), str)  # Bullish
    assert isinstance(output._trend_color(False), str)  # Bearish
