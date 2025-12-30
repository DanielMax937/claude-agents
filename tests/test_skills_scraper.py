"""Tests for Scraper skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_scraper_skill_name():
    """ScraperSkill should have correct skill name."""
    from commodity_pipeline.skills.scraper import ScraperSkill

    skill = ScraperSkill()
    assert skill.skill_name == "scraper"


def test_scraper_get_news_parses_result():
    """get_news should parse JSON into NewsItem objects."""
    from commodity_pipeline.skills.scraper import ScraperSkill
    from commodity_pipeline.models import NewsItem

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = [
        {
            "title": "螺纹钢期货上涨",
            "source": "eastmoney",
            "url": "https://example.com/1",
            "published": "2024-12-30",
            "summary": "市场看涨",
            "sentiment": "positive"
        }
    ]

    with patch.object(ScraperSkill, '_run', return_value=mock_result):
        skill = ScraperSkill()
        news = skill.get_news("螺纹钢", sources=["eastmoney"])

        assert len(news) == 1
        assert isinstance(news[0], NewsItem)
        assert news[0].title == "螺纹钢期货上涨"
