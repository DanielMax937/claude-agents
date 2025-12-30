"""Tests for China Futures skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock


def test_china_futures_skill_name():
    """ChinaFuturesSkill should have correct skill name."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill

    skill = ChinaFuturesSkill()
    assert skill.skill_name == "china-futures"


def test_china_futures_get_main_contracts_parses_result():
    """get_main_contracts should parse JSON into Commodity objects."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
    from commodity_pipeline.models import Commodity

    # Mock the skill result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = [
        {
            "code": "rb2501",
            "name": "螺纹钢",
            "exchange": "SHFE",
            "main_contract": "rb2501",
            "price": 3500.0,
            "change_1d": 1.5,
            "change_3d": 2.0,
            "change_5d": -0.5
        }
    ]

    with patch.object(ChinaFuturesSkill, '_run', return_value=mock_result):
        skill = ChinaFuturesSkill()
        commodities = skill.get_main_contracts()

        assert len(commodities) == 1
        assert isinstance(commodities[0], Commodity)
        assert commodities[0].code == "rb2501"
        assert commodities[0].price == 3500.0
