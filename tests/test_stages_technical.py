"""Tests for Technical stage."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_technical_stage_analyze_one():
    """_analyze_one should get OHLCV and run TA for one commodity."""
    from commodity_pipeline.stages.technical import TechnicalStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, OHLCVBar, TechnicalSignals, TrendDirection

    config = PipelineConfig()
    stage = TechnicalStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5)

    # Mock the skill calls
    mock_ohlcv = [
        OHLCVBar(date(2024, 12, 30), 3500, 3550, 3480, 3520, 100000)
    ]
    mock_signals = TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )

    with patch.object(stage.futures_skill, 'get_ohlcv', return_value=mock_ohlcv):
        with patch.object(stage.ta_skill, 'analyze', return_value=mock_signals):
            result = stage._analyze_one(commodity)

            assert result.commodity_code == "rb2501"
            assert result.overall_trend == TrendDirection.BULLISH
