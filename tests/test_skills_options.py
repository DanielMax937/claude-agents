"""Tests for Options skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock


def test_options_skill_name():
    """OptionsSkill should have correct skill name."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    skill = OptionsSkill()
    assert skill.skill_name == "options"


def test_options_skill_calc_greeks():
    """calc_greeks should parse Greeks from text output."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    # Simulate text output from greeks.py
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = """
Inputs: S=3500, K=3600, T=0.1000y, r=2.0%, σ=25.0%, CALL

==================================================
OPTIONS GREEKS - CALL
==================================================

📊 First-Order Greeks:
  Delta (Δ):        0.4500  (price change per $1 underlying)
  Gamma (Γ):      0.020000  (delta change per $1 underlying)
  Theta (Θ):       -5.0000  (daily time decay)
  Vega (ν):        10.0000  (price change per 1% vol)
  Rho (ρ):          0.5000  (price change per 1% rate)
"""

    with patch.object(OptionsSkill, '_run', return_value=mock_result):
        skill = OptionsSkill()
        greeks = skill.calc_greeks(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, vol=0.25, option_type="call"
        )

        assert greeks["delta"] == 0.45
        assert greeks["gamma"] == 0.02
        assert greeks["theta"] == -5.0
        assert greeks["vega"] == 10.0
        assert greeks["rho"] == 0.5


def test_options_skill_calc_bs_price():
    """calc_bs_price should parse price from text output."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    # Simulate text output from pricing.py
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = """
==================================================
Option Pricing - BS Model
==================================================

Inputs:
  Underlying:  3,500.00
  Strike:      3,600.00
  Time:        0.1000 years (36 days)
  Rate:        2.00%
  Volatility:  25.0%
  Type:        CALL

Results:
  Price:       48.5000
  Delta (Δ):   0.4500
"""

    with patch.object(OptionsSkill, '_run', return_value=mock_result):
        skill = OptionsSkill()
        price = skill.calc_bs_price(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, vol=0.25, option_type="call"
        )

        assert price == 48.5


def test_options_skill_calc_iv():
    """calc_iv should parse IV from JSON output."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    # iv.py supports --json flag
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = {
        "implied_volatility": 0.25,
        "implied_volatility_pct": 25.0,
        "method": "newton",
        "success": True
    }

    with patch.object(OptionsSkill, '_run', return_value=mock_result):
        skill = OptionsSkill()
        iv = skill.calc_iv(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, market_price=50.0, option_type="call"
        )

        assert iv == 0.25


def test_options_skill_parse_greeks_handles_missing_values():
    """_parse_greeks_output should return defaults for missing values."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    skill = OptionsSkill()

    # Empty output should return all zeros
    greeks = skill._parse_greeks_output("")
    assert greeks["delta"] == 0.0
    assert greeks["gamma"] == 0.0

    # Partial output
    greeks = skill._parse_greeks_output("Delta (Δ): 0.55")
    assert greeks["delta"] == 0.55
    assert greeks["gamma"] == 0.0
