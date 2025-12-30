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


def test_integration_review_mode_flow():
    """Review mode pipeline should analyze holdings and produce recommendations."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import (
        Commodity, TechnicalSignals, TrendDirection, OptionContract, NewsItem
    )
    from datetime import timedelta

    holdings = [
        {"code": "CU2501-C-75000", "quantity": 2, "avg_cost": 1200},
        {"code": "CU2501-P-73000", "quantity": 1, "avg_cost": 800}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        config = PipelineConfig(mode="review", holdings=holdings, output_dir=tmpdir)
        pipeline = Pipeline(config)

        # Mock stage results
        mock_commodities = {
            "CU": Commodity("CU", "铜", "SHFE", "cu2501", 74520, 1.5, 2.0, -0.5)
        }

        mock_technical = {
            "CU": TechnicalSignals(
                "CU", "buy", "buy", 58.0, "neutral", "middle",
                "buy", 150.0, "up", "buy", TrendDirection.BULLISH, 7
            )
        }

        mock_options = {
            "CU": [
                OptionContract(
                    "CU2501-C-75000", "CU", 75000, date.today() + timedelta(days=45), "call",
                    1450, 1000, 0.185, 0.52, 0.00008, -12.3, 42.1, 0.15, 1430, 20
                ),
                OptionContract(
                    "CU2501-P-73000", "CU", 73000, date.today() + timedelta(days=45), "put",
                    850, 500, 0.20, -0.35, 0.00006, -8.5, 25.0, 0.12, 830, 20
                )
            ]
        }

        mock_news = {"CU": [
            NewsItem("Copper demand rises", "eastmoney", "http://1", date.today(), sentiment="positive")
        ]}

        # Patch stages
        with patch.object(pipeline.screening_stage, 'run_for_symbols', return_value=mock_commodities):
            with patch.object(pipeline.technical_stage, 'run', new_callable=AsyncMock, return_value=mock_technical):
                with patch.object(pipeline.options_stage, 'run', new_callable=AsyncMock, return_value=mock_options):
                    with patch.object(pipeline.news_stage, 'run', new_callable=AsyncMock, return_value=mock_news):
                        # Run pipeline
                        result = asyncio.get_event_loop().run_until_complete(pipeline.run())

                        # Verify structure
                        assert "positions" in result
                        assert len(result["positions"]) == 2

                        # Verify position analysis
                        pos1 = next(p for p in result["positions"] if p["position_code"] == "CU2501-C-75000")
                        assert "signal" in pos1
                        assert "confidence" in pos1
                        assert "recommendation" in pos1
                        assert "reason" in pos1

                        # Verify scores
                        assert "scores" in pos1
                        assert "greeks" in pos1["scores"]
                        assert "technical" in pos1["scores"]

                        # Verify metrics
                        assert "metrics" in pos1
                        assert "delta" in pos1["metrics"]
                        assert "dte" in pos1["metrics"]


def test_integration_review_mode_terminal_output():
    """Review mode terminal output should format positions correctly."""
    from commodity_pipeline.pipeline import Pipeline
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity

    holdings = [{"code": "CU2501-C-75000", "quantity": 2, "avg_cost": 1200}]

    config = PipelineConfig(mode="review", holdings=holdings)
    pipeline = Pipeline(config)

    # Mock review stage result - must be async
    async def mock_review(*args, **kwargs):
        return [
            {
                "position_code": "CU2501-C-75000",
                "signal": "bullish",
                "confidence": 0.75,
                "scores": {"greeks": 55, "technical": 80, "time": 65, "news": 70},
                "metrics": {"delta": 0.52, "spot": 74520, "dte": 45, "iv": 18.5},
                "recommendation": "HOLD",
                "reason": "Strong bullish setup with optimal time to expiry."
            }
        ]

    pipeline.position_review_stage.run = mock_review

    # Mock commodity - must exist for pipeline to continue
    mock_commodity = {
        "CU": Commodity("CU", "铜", "SHFE", "cu2501", 74520, 1.5, 2.0, -0.5)
    }

    # Mock other stages
    with patch.object(pipeline.screening_stage, 'run_for_symbols', return_value=mock_commodity):
        with patch.object(pipeline.technical_stage, 'run', new_callable=AsyncMock, return_value={}):
            with patch.object(pipeline.options_stage, 'run', new_callable=AsyncMock, return_value={}):
                with patch.object(pipeline.news_stage, 'run', new_callable=AsyncMock, return_value={}):
                    result = asyncio.get_event_loop().run_until_complete(pipeline.run())

                    # Generate terminal output
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = buffer = io.StringIO()

                    pipeline.output_terminal(result)

                    output = buffer.getvalue()
                    sys.stdout = old_stdout

                    # Verify output contains key elements
                    assert "POSITION REVIEW REPORT" in output
                    assert "CU2501-C-75000" in output
                    assert "HOLD" in output
                    assert "bullish" in output
