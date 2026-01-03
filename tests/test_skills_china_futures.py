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
            "code": "RB",
            "symbol": "RB2501",
            "name": "螺纹钢",
            "exchange": "SHFE",
            "price": 3500.0,
            "pct_change": 1.5,
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
        assert commodities[0].code == "RB"
        assert commodities[0].main_contract == "RB2501"
        assert commodities[0].price == 3500.0


def test_china_futures_get_ohlcv_parses_result():
    """get_ohlcv should parse JSON into OHLCVBar objects."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
    from commodity_pipeline.models import OHLCVBar

    # Mock the skill result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = [
        {
            "date": "2025-01-02",
            "open": 3500.0,
            "high": 3550.0,
            "low": 3480.0,
            "close": 3520.0,
            "volume": 100000
        }
    ]

    with patch.object(ChinaFuturesSkill, '_run', return_value=mock_result):
        skill = ChinaFuturesSkill()
        bars = skill.get_ohlcv("CU", days=15)

        assert len(bars) == 1
        assert isinstance(bars[0], OHLCVBar)
        assert bars[0].open == 3500.0
        assert bars[0].close == 3520.0
        assert bars[0].volume == 100000


def test_china_futures_get_quote():
    """get_quote should return quote dict for a commodity."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = {
        "symbol": "CU2503",
        "code": "CU",
        "name": "沪铜",
        "price": 75000.0,
        "pct_change": 0.5
    }

    with patch.object(ChinaFuturesSkill, '_run', return_value=mock_result):
        skill = ChinaFuturesSkill()
        quote = skill.get_quote("CU")

        assert quote["symbol"] == "CU2503"
        assert quote["price"] == 75000.0


def test_china_futures_get_options_list():
    """get_options_list should return list of options."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = [
        {"code": "CU2503C75000", "strike": 75000, "type": "call", "volume": 100},
        {"code": "CU2503P74000", "strike": 74000, "type": "put", "volume": 50}
    ]

    with patch.object(ChinaFuturesSkill, '_run', return_value=mock_result):
        skill = ChinaFuturesSkill()
        options = skill.get_options_list("CU")

        assert len(options) == 2
        assert options[0]["code"] == "CU2503C75000"
        assert options[1]["type"] == "put"
