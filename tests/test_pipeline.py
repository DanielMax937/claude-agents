"""Tests for the main pipeline entry point."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import date
import asyncio


def test_pipeline_run_orchestrates_all_stages():
    """Pipeline.run() should orchestrate all stages in order."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection, NewsItem
    )

    config = PipelineConfig()
    pipeline = Pipeline(config)

    # Mock all stage results
    mock_commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
    ]
    mock_technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}
    mock_options = {"rb2501": []}
    mock_news = {"rb2501": []}
    mock_alerts = []
    mock_strategies = {"rb2501": []}

    with patch.object(pipeline.screening_stage, 'run', new_callable=AsyncMock, return_value=mock_commodities):
        with patch.object(pipeline.technical_stage, 'run', new_callable=AsyncMock, return_value=mock_technical):
            with patch.object(pipeline.options_stage, 'run', new_callable=AsyncMock, return_value=mock_options):
                with patch.object(pipeline.news_stage, 'run', new_callable=AsyncMock, return_value=mock_news):
                    with patch.object(pipeline.alerts_stage, 'run', new_callable=AsyncMock, return_value=mock_alerts):
                        with patch.object(pipeline.strategy_stage, 'run', new_callable=AsyncMock, return_value=mock_strategies):
                            result = asyncio.get_event_loop().run_until_complete(pipeline.run())

                            assert "commodities" in result
                            assert "technical" in result
                            assert "options" in result
                            assert "news" in result
                            assert "alerts" in result
                            assert "strategies" in result

                            assert len(result["commodities"]) == 1
                            assert result["commodities"][0].code == "rb2501"


def test_pipeline_output_terminal():
    """Pipeline should output to terminal when enabled."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection

    config = PipelineConfig()
    pipeline = Pipeline(config)

    result = {
        "commodities": [Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)],
        "technical": {"rb2501": TechnicalSignals(
            "rb2501", "buy", "buy", 65.0, "neutral", "middle",
            "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
        )},
        "options": {},
        "news": {},
        "alerts": [],
        "strategies": {}
    }

    with patch.object(pipeline.terminal_output, 'format_all', return_value="Report") as mock_format:
        with patch.object(pipeline.terminal_output, 'print_report') as mock_print:
            pipeline.output_terminal(result)

            mock_format.assert_called_once()
            mock_print.assert_called_once_with("Report")


def test_pipeline_save_reports():
    """Pipeline should save markdown and JSON reports."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(output_dir=tmpdir)
        pipeline = Pipeline(config)

        result = {
            "commodities": [Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)],
            "technical": {"rb2501": TechnicalSignals(
                "rb2501", "buy", "buy", 65.0, "neutral", "middle",
                "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
            )},
            "options": {},
            "news": {},
            "alerts": [],
            "strategies": {}
        }

        pipeline.save_reports(result)

        # Check files were created
        files = os.listdir(tmpdir)
        assert any(f.endswith(".md") for f in files)
        assert any(f.endswith(".json") for f in files)
