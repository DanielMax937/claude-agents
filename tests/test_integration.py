"""Integration tests for the full pipeline flow."""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, AsyncMock
from datetime import date


def test_integration_pipeline_orchestrates_stages():
    """Pipeline should orchestrate all stages in sequence."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(output_dir=tmpdir)
        pipeline = Pipeline(config)

        # Mock all stage results
        mock_commodities = [
            Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
        ]

        mock_technical = {"rb2501": TechnicalSignals(
            "rb2501", "buy", "buy", 65.0, "neutral", "middle",
            "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
        )}

        mock_options = {"rb2501": [
            OptionContract(
                "rb2501C3500", "rb2501", 3500.0, date(2025, 1, 15), "call",
                50.0, 1000, 0.25, 0.55, 0.02, -5.0, 10.0, 0.5, 48.0, 2.0
            )
        ]}

        mock_news = {"rb2501": [
            NewsItem("价格上涨", "eastmoney", "http://test.com", date.today())
        ]}

        mock_alerts = [
            NewsItem("市场警报", "gmail", "http://gmail.com", date.today())
        ]

        mock_strategies = {"rb2501": [
            StrategyRecommendation(
                "Long Call", "directional",
                [{"action": "buy", "option": "rb2501C3500"}],
                1000.0, 50.0, [3550.0], "Bullish", 7
            )
        ]}

        # Patch all stages
        with patch.object(pipeline.screening_stage, 'run', new_callable=AsyncMock, return_value=mock_commodities):
            with patch.object(pipeline.technical_stage, 'run', new_callable=AsyncMock, return_value=mock_technical):
                with patch.object(pipeline.options_stage, 'run', new_callable=AsyncMock, return_value=mock_options):
                    with patch.object(pipeline.news_stage, 'run', new_callable=AsyncMock, return_value=mock_news):
                        with patch.object(pipeline.alerts_stage, 'run_filtered', new_callable=AsyncMock, return_value=mock_alerts):
                            with patch.object(pipeline.strategy_stage, 'run', new_callable=AsyncMock, return_value=mock_strategies):
                                # Run pipeline
                                result = asyncio.get_event_loop().run_until_complete(pipeline.run())

                                # Verify structure
                                assert len(result["commodities"]) == 1
                                assert "rb2501" in result["technical"]
                                assert "rb2501" in result["options"]
                                assert len(result["options"]["rb2501"]) == 1
                                assert len(result["alerts"]) == 1
                                assert "rb2501" in result["strategies"]


def test_integration_pipeline_produces_reports():
    """Pipeline should produce markdown and JSON reports."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(output_dir=tmpdir)
        pipeline = Pipeline(config)

        # Create minimal result
        result = {
            "commodities": [
                Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
            ],
            "technical": {"rb2501": TechnicalSignals(
                "rb2501", "buy", "buy", 65.0, "neutral", "middle",
                "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
            )},
            "options": {},
            "news": {},
            "alerts": [],
            "strategies": {}
        }

        # Save reports
        pipeline.save_reports(result)

        # Verify files exist
        files = os.listdir(tmpdir)
        md_files = [f for f in files if f.endswith(".md")]
        json_files = [f for f in files if f.endswith(".json")]

        assert len(md_files) >= 1, "No markdown report found"
        assert len(json_files) >= 1, "No JSON report found"

        # Verify content
        md_path = os.path.join(tmpdir, md_files[0])
        with open(md_path, "r") as f:
            content = f.read()
            assert "rb2501" in content
            assert "螺纹钢" in content

        json_path = os.path.join(tmpdir, json_files[0])
        with open(json_path, "r") as f:
            import json
            data = json.load(f)
            assert data["commodities"][0]["code"] == "rb2501"


def test_integration_pipeline_handles_empty_commodities():
    """Pipeline should handle case with no commodities gracefully."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(output_dir=tmpdir)
        pipeline = Pipeline(config)

        # Mock screening to return empty list
        with patch.object(pipeline.screening_stage, 'run', new_callable=AsyncMock, return_value=[]):
            result = asyncio.get_event_loop().run_until_complete(pipeline.run())

            assert result["commodities"] == []
            assert result["technical"] == {}
            assert result["strategies"] == {}


def test_integration_terminal_output():
    """Terminal output should produce formatted string."""
    from commodity_pipeline.output.terminal import TerminalOutput
    from commodity_pipeline.models import Commodity, TechnicalSignals, TrendDirection

    output = TerminalOutput(use_colors=False)

    commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)
    ]
    technical = {"rb2501": TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )}

    report = output.format_all(commodities, technical, {}, {}, {}, [])

    assert "rb2501" in report
    assert "螺纹钢" in report
    assert "BULLISH" in report


def test_integration_json_output_serialization():
    """JSON output should serialize all data types correctly."""
    from commodity_pipeline.output.json_output import JSONOutput
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection,
        OptionContract, NewsItem, StrategyRecommendation
    )
    import json

    output = JSONOutput()

    commodities = [Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 2.5, 5.0, -1.0)]
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
    news = {"rb2501": [NewsItem("Test", "source", "http://test", date.today())]}
    strategies = {"rb2501": [
        StrategyRecommendation("Long Call", "directional", [], 1000, 50, [], "Test", 7)
    ]}
    alerts = [NewsItem("Alert", "gmail", "http://alert", date.today())]

    json_str = output.to_json(commodities, technical, options, news, strategies, alerts)

    # Should be valid JSON
    data = json.loads(json_str)

    assert data["commodities"][0]["code"] == "rb2501"
    assert data["commodities"][0]["technical"]["overall_trend"] == "bullish"
    assert len(data["commodities"][0]["options"]) == 1
    assert data["commodities"][0]["options"][0]["expiry"] == "2025-01-15"
