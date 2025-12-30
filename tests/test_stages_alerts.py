"""Tests for Alerts stage (Gmail alerts)."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_alerts_stage_get_alerts():
    """run() should get Gmail alerts and return them."""
    from commodity_pipeline.stages.alerts import AlertsStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import NewsItem

    config = PipelineConfig()
    stage = AlertsStage(config)

    mock_alerts = [
        NewsItem("市场警报1", "gmail", "http://alert1", date(2024, 12, 30), summary="重要"),
        NewsItem("市场警报2", "gmail", "http://alert2", date(2024, 12, 30)),
    ]

    with patch.object(stage.gmail_skill, 'get_alerts', return_value=mock_alerts):
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(stage.run())

        assert len(result) == 2
        assert result[0].title == "市场警报1"
        assert result[0].source == "gmail"


def test_alerts_stage_filters_by_keywords():
    """AlertsStage should filter alerts matching commodity keywords."""
    from commodity_pipeline.stages.alerts import AlertsStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, NewsItem

    config = PipelineConfig()
    stage = AlertsStage(config)

    commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5),
        Commodity("cu2501", "铜", "SHFE", "cu2501", 70000, -0.5, 1.0, 2.0),
    ]

    all_alerts = [
        NewsItem("螺纹钢价格上涨", "gmail", "http://1", date.today()),  # Matches rb
        NewsItem("铜矿新闻", "gmail", "http://2", date.today()),       # Matches cu
        NewsItem("天气预报", "gmail", "http://3", date.today()),       # No match
    ]

    with patch.object(stage.gmail_skill, 'get_alerts', return_value=all_alerts):
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            stage.run_filtered(commodities)
        )

        # Should only return alerts matching commodity names
        assert len(result) == 2
        titles = [n.title for n in result]
        assert "螺纹钢价格上涨" in titles
        assert "铜矿新闻" in titles
        assert "天气预报" not in titles
