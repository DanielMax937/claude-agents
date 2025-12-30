"""Tests for Markdown output formatter."""
import pytest
from datetime import date
import tempfile
import os


def test_markdown_output_format_commodity():
    """format_commodity should create proper markdown sections."""
    from commodity_pipeline.output.markdown import MarkdownOutput
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )

    output = MarkdownOutput()

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

    news = [NewsItem("价格上涨", "eastmoney", "http://example.com", date.today())]

    strategies = [
        StrategyRecommendation(
            "Long Call", "directional",
            [{"action": "buy", "option": "rb2501C3500"}],
            float("inf"), 50.0, [3550.0],
            "Bullish momentum", 7
        )
    ]

    result = output.format_commodity(commodity, technical, options, news, strategies)

    # Should be valid markdown
    assert "## rb2501" in result or "# rb2501" in result
    assert "螺纹钢" in result
    assert "| " in result  # Tables
    assert "Long Call" in result


def test_markdown_output_format_all():
    """format_all should create complete markdown document."""
    from commodity_pipeline.output.markdown import MarkdownOutput
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection, NewsItem
    )

    output = MarkdownOutput()

    commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
    ]

    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    result = output.format_all(commodities, technical, {}, {}, {}, [])

    # Should have proper markdown structure
    assert "# Commodity Analysis Report" in result
    assert "rb2501" in result


def test_markdown_output_save_to_file():
    """save() should write markdown to file."""
    from commodity_pipeline.output.markdown import MarkdownOutput
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection

    output = MarkdownOutput()

    commodities = [Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)]
    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "report.md")
        output.save(filepath, commodities, technical, {}, {}, {}, [])

        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            content = f.read()
            assert "rb2501" in content
            assert "# Commodity Analysis Report" in content
