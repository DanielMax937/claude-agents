"""Tests for Gmail skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_gmail_skill_name():
    """GmailSkill should have correct skill name."""
    from commodity_pipeline.skills.gmail import GmailSkill

    skill = GmailSkill()
    assert skill.skill_name == "gmail-reader"


def test_gmail_get_alerts():
    """get_alerts should return list of NewsItem objects."""
    from commodity_pipeline.skills.gmail import GmailSkill
    from commodity_pipeline.models import NewsItem

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = [
        {
            "title": "Google Alert - 螺纹钢",
            "source": "gmail",
            "url": "https://mail.google.com/1",
            "published": "2024-12-30",
            "summary": "New article about 螺纹钢"
        }
    ]

    with patch.object(GmailSkill, '_run', return_value=mock_result):
        skill = GmailSkill()
        alerts = skill.get_alerts()

        assert len(alerts) == 1
        assert isinstance(alerts[0], NewsItem)
        assert alerts[0].source == "gmail"
