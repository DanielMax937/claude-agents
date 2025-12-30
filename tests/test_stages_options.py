"""Tests for Options stage."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_options_stage_process_one():
    """_process_one should get options chain and calculate Greeks/IV/BS for top contracts."""
    from commodity_pipeline.stages.options import OptionsStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, OptionContract

    config = PipelineConfig(top_options_by_volume=2, risk_free_rate=0.02)
    stage = OptionsStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5)

    # Mock the raw options chain (from china-futures skill)
    mock_chain = [
        {"code": "rb2501C3500", "strike": 3500, "expiry": "2025-01-15",
         "type": "call", "price": 50.0, "volume": 1000},
        {"code": "rb2501C3600", "strike": 3600, "expiry": "2025-01-15",
         "type": "call", "price": 30.0, "volume": 500},
        {"code": "rb2501P3400", "strike": 3400, "expiry": "2025-01-15",
         "type": "put", "price": 40.0, "volume": 800},
    ]

    # Mock Greeks result
    mock_greeks = {"delta": 0.55, "gamma": 0.02, "theta": -5.0, "vega": 10.0, "rho": 0.5}

    with patch.object(stage.futures_skill, 'get_options_chain', return_value=mock_chain):
        with patch.object(stage.options_skill, 'calc_greeks', return_value=mock_greeks):
            with patch.object(stage.options_skill, 'calc_iv', return_value=0.25):
                with patch.object(stage.options_skill, 'calc_bs_price', return_value=48.0):
                    result = stage._process_one(commodity)

                    # Should return top 2 by volume
                    assert len(result) == 2

                    # First should be highest volume (1000)
                    assert result[0].code == "rb2501C3500"
                    assert result[0].volume == 1000
                    assert result[0].iv == 0.25
                    assert result[0].delta == 0.55
                    assert result[0].bs_value == 48.0
                    assert result[0].mispricing == 2.0  # 50 - 48


def test_options_stage_filters_by_volume():
    """Stage should keep only top N contracts by volume."""
    from commodity_pipeline.stages.options import OptionsStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity

    config = PipelineConfig(top_options_by_volume=1)
    stage = OptionsStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5)

    mock_chain = [
        {"code": "opt1", "strike": 3500, "expiry": "2025-01-15",
         "type": "call", "price": 50.0, "volume": 100},
        {"code": "opt2", "strike": 3600, "expiry": "2025-01-15",
         "type": "call", "price": 30.0, "volume": 500},  # Highest volume
    ]

    mock_greeks = {"delta": 0.5, "gamma": 0.01, "theta": -1.0, "vega": 5.0, "rho": 0.2}

    with patch.object(stage.futures_skill, 'get_options_chain', return_value=mock_chain):
        with patch.object(stage.options_skill, 'calc_greeks', return_value=mock_greeks):
            with patch.object(stage.options_skill, 'calc_iv', return_value=0.20):
                with patch.object(stage.options_skill, 'calc_bs_price', return_value=30.0):
                    result = stage._process_one(commodity)

                    # Should only keep top 1
                    assert len(result) == 1
                    assert result[0].code == "opt2"  # Highest volume
