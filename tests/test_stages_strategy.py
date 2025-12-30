"""Tests for Strategy stage."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_strategy_stage_generate_for_commodity():
    """_generate_for_commodity should create strategy recommendations."""
    from commodity_pipeline.stages.strategy import StrategyStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )

    config = PipelineConfig()
    stage = StrategyStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5)

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

    news = [NewsItem("价格上涨", "eastmoney", "http://1", date.today(), sentiment="positive")]

    result = stage._generate_for_commodity(commodity, technical, options, news)

    # Should generate at least one strategy
    assert len(result) >= 1
    assert isinstance(result[0], StrategyRecommendation)
    assert result[0].confidence >= 1 and result[0].confidence <= 10


def test_strategy_stage_bullish_generates_call_strategy():
    """Bullish trend should generate long call or bull spread strategies."""
    from commodity_pipeline.stages.strategy import StrategyStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem
    )

    config = PipelineConfig()
    stage = StrategyStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 5.0, 8.0, 10.0)

    # Strong bullish signals
    technical = TechnicalSignals(
        "rb2501", "buy", "buy", 35.0, "oversold", "below_lower",
        "buy", 50.0, "up", "buy", TrendDirection.BULLISH, 9
    )

    options = [
        OptionContract(
            "rb2501C3500", "rb2501", 3500.0, date(2025, 1, 15), "call",
            50.0, 1000, 0.25, 0.55, 0.02, -5.0, 10.0, 0.5, 48.0, 2.0
        )
    ]

    news = [NewsItem("市场看涨", "eastmoney", "http://1", date.today(), sentiment="positive")]

    result = stage._generate_for_commodity(commodity, technical, options, news)

    # Should have directional bullish strategy
    strategy_types = [r.type for r in result]
    strategy_names = [r.name.lower() for r in result]

    # At least one bullish/directional strategy
    assert "directional" in strategy_types or any(
        "call" in name or "bull" in name for name in strategy_names
    )


def test_strategy_stage_bearish_generates_put_strategy():
    """Bearish trend should generate long put or bear spread strategies."""
    from commodity_pipeline.stages.strategy import StrategyStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem
    )

    config = PipelineConfig()
    stage = StrategyStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, -5.0, -8.0, -10.0)

    # Strong bearish signals
    technical = TechnicalSignals(
        "rb2501", "sell", "sell", 75.0, "overbought", "above_upper",
        "sell", 50.0, "down", "sell", TrendDirection.BEARISH, 9
    )

    options = [
        OptionContract(
            "rb2501P3500", "rb2501", 3500.0, date(2025, 1, 15), "put",
            60.0, 1000, 0.28, -0.45, 0.02, -5.0, 10.0, -0.5, 58.0, 2.0
        )
    ]

    news = [NewsItem("市场看跌", "eastmoney", "http://1", date.today(), sentiment="negative")]

    result = stage._generate_for_commodity(commodity, technical, options, news)

    strategy_names = [r.name.lower() for r in result]

    # At least one bearish strategy
    assert any("put" in name or "bear" in name for name in strategy_names)
