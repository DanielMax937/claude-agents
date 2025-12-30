"""Tests for JSON output formatter."""
import pytest
import json
from datetime import date
import tempfile
import os


def test_json_output_to_dict():
    """to_dict should serialize all data to a dict."""
    from commodity_pipeline.output.json_output import JSONOutput
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )

    output = JSONOutput()

    commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
    ]

    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    options = {"rb2501": [
        OptionContract(
            "rb2501C3500", "rb2501", 3500.0, date(2025, 1, 15), "call",
            50.0, 1000, 0.25, 0.55, 0.02, -5.0, 10.0, 0.5, 48.0, 2.0
        )
    ]}

    news = {"rb2501": [NewsItem("价格上涨", "eastmoney", "http://1", date.today())]}

    strategies = {"rb2501": [
        StrategyRecommendation(
            "Long Call", "directional",
            [{"action": "buy", "option": "rb2501C3500"}],
            1000.0, 50.0, [3550.0],
            "Bullish momentum", 7
        )
    ]}

    alerts = [NewsItem("Alert!", "gmail", "http://alert", date.today())]

    result = output.to_dict(commodities, technical, options, news, strategies, alerts)

    # Should be a proper dict
    assert isinstance(result, dict)
    assert "commodities" in result
    assert "alerts" in result
    assert "generated_at" in result

    # Should have commodity data
    assert len(result["commodities"]) == 1
    assert result["commodities"][0]["code"] == "rb2501"
    assert result["commodities"][0]["technical"]["overall_trend"] == "bullish"


def test_json_output_to_json():
    """to_json should return valid JSON string."""
    from commodity_pipeline.output.json_output import JSONOutput
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection

    output = JSONOutput()

    commodities = [Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)]
    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    result = output.to_json(commodities, technical, {}, {}, {}, [])

    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed["commodities"][0]["code"] == "rb2501"


def test_json_output_save():
    """save() should write JSON to file."""
    from commodity_pipeline.output.json_output import JSONOutput
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection

    output = JSONOutput()

    commodities = [Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)]
    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "report.json")
        output.save(filepath, commodities, technical, {}, {}, {}, [])

        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)
            assert data["commodities"][0]["code"] == "rb2501"
