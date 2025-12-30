"""Tests for Options skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock


def test_options_skill_name():
    """OptionsSkill should have correct skill name."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    skill = OptionsSkill()
    assert skill.skill_name == "options"


def test_options_skill_calc_greeks():
    """calc_greeks should return Greeks dictionary."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = {
        "delta": 0.45,
        "gamma": 0.02,
        "theta": -5.0,
        "vega": 10.0,
        "rho": 0.5
    }

    with patch.object(OptionsSkill, '_run', return_value=mock_result):
        skill = OptionsSkill()
        greeks = skill.calc_greeks(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, vol=0.25, option_type="call"
        )

        assert greeks["delta"] == 0.45
        assert greeks["gamma"] == 0.02


def test_options_skill_calc_bs_price():
    """calc_bs_price should return Black-Scholes price."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = {"price": 48.5}

    with patch.object(OptionsSkill, '_run', return_value=mock_result):
        skill = OptionsSkill()
        price = skill.calc_bs_price(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, vol=0.25, option_type="call"
        )

        assert price == 48.5
