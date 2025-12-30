"""Tests for News stage."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_news_stage_get_news_for_commodity():
    """_get_news_for_commodity should scrape news for a commodity's name."""
    from commodity_pipeline.stages.news import NewsStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, NewsItem

    config = PipelineConfig(
        news_sources=("eastmoney", "sina"),
        max_news_per_source=3
    )
    stage = NewsStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5)

    mock_news = [
        NewsItem("螺纹钢价格上涨", "eastmoney", "http://example.com/1", date(2024, 12, 30)),
        NewsItem("钢铁行业分析", "sina", "http://example.com/2", date(2024, 12, 29)),
    ]

    with patch.object(stage.scraper_skill, 'get_news', return_value=mock_news):
        result = stage._get_news_for_commodity(commodity)

        assert len(result) == 2
        assert result[0].title == "螺纹钢价格上涨"
        # Verify the scraper was called with commodity name
        stage.scraper_skill.get_news.assert_called_once_with(
            "螺纹钢",
            sources=["eastmoney", "sina"],
            max_per_source=3
        )


def test_news_stage_aggregates_news():
    """run() should aggregate news for all commodities."""
    from commodity_pipeline.stages.news import NewsStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, NewsItem

    config = PipelineConfig()
    stage = NewsStage(config)

    commodities = [
        Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5),
        Commodity("cu2501", "铜", "SHFE", "cu2501", 70000, -0.5, 1.0, 2.0),
    ]

    # Each commodity gets different news
    def mock_get_news(keyword, sources=None, max_per_source=5):
        if "螺纹钢" in keyword:
            return [NewsItem("钢铁新闻", "eastmoney", "http://1", date.today())]
        else:
            return [NewsItem("铜矿新闻", "eastmoney", "http://2", date.today())]

    with patch.object(stage.scraper_skill, 'get_news', side_effect=mock_get_news):
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(stage.run(commodities))

        assert "rb2501" in result
        assert "cu2501" in result
        assert len(result["rb2501"]) == 1
        assert result["rb2501"][0].title == "钢铁新闻"
        assert result["cu2501"][0].title == "铜矿新闻"
