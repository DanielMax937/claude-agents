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


def test_terminal_output_format_position_review():
    """format_position_review should output position analysis with recommendation."""
    from commodity_pipeline.output.terminal import TerminalOutput
    from datetime import timedelta

    output = TerminalOutput(use_colors=False)

    position_result = {
        "position_code": "CU2501-C-75000",
        "signal": "bullish",
        "confidence": 0.75,
        "scores": {"greeks": 50, "technical": 80, "time": 60, "news": 70},
        "metrics": {
            "delta": 0.52,
            "gamma": 0.00008,
            "theta": -12.3,
            "vega": 42.1,
            "iv": 18.5,
            "spot": 74520,
            "strike": 75000,
            "dte": 16,
            "itm_amount": 0,
            "rsi": 58.0,
            "trend": "bullish"
        },
        "recommendation": "HOLD",
        "reason": "Greeks: 50/100 - Moderate delta exposure. Technical: 80/100 - Strong bullish setup."
    }

    result = output.format_position_review([position_result])

    # Should contain key information
    assert "CU2501-C-75000" in result
    assert "HOLD" in result
    assert "bullish" in result
    assert "75%" in result or "0.75" in result
    assert "Greeks" in result or "greeks" in result
    assert "Technical" in result or "technical" in result


def test_terminal_output_format_position_review_multiple():
    """format_position_review should handle multiple positions."""
    from commodity_pipeline.output.terminal import TerminalOutput

    output = TerminalOutput(use_colors=False)

    positions = [
        {
            "position_code": "CU2501-C-75000",
            "signal": "bullish",
            "confidence": 0.80,
            "scores": {"greeks": 60, "technical": 85, "time": 70, "news": 75},
            "metrics": {
                "delta": 0.52, "gamma": 0.00008, "theta": -12.3, "vega": 42.1,
                "iv": 18.5, "spot": 74520, "strike": 75000, "dte": 45, "itm_amount": 0
            },
            "recommendation": "HOLD",
            "reason": "Strong technical setup, optimal time to expiry."
        },
        {
            "position_code": "CU2501-P-73000",
            "signal": "bearish",
            "confidence": 0.35,
            "scores": {"greeks": 30, "technical": 40, "time": 30, "news": 35},
            "metrics": {
                "delta": -0.25, "gamma": 0.00006, "theta": -8.5, "vega": 25.0,
                "iv": 20.0, "spot": 74520, "strike": 73000, "dte": 5, "itm_amount": 0
            },
            "recommendation": "CLOSE",
            "reason": "Low scores across all dimensions, urgent expiry."
        }
    ]

    result = output.format_position_review(positions)

    assert "CU2501-C-75000" in result
    assert "CU2501-P-73000" in result
    assert "HOLD" in result
    assert "CLOSE" in result


def test_terminal_recommendation_color():
    """_recommendation_color should return appropriate colors."""
    from commodity_pipeline.output.terminal import TerminalOutput

    output = TerminalOutput(use_colors=True)

    # Check color methods exist
    assert isinstance(output._recommendation_color("HOLD"), str)
    assert isinstance(output._recommendation_color("ADJUST"), str)
    assert isinstance(output._recommendation_color("CLOSE"), str)
