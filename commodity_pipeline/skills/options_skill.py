"""Wrapper for options skill (Greeks, IV, Black-Scholes pricing).

Note: The options skill scripts have different output formats:
- pricing.py: Text output only (no --json flag)
- greeks.py: Text output only (no --json flag)
- iv.py: Supports --json flag
"""
import re
import json
from typing import Dict, Optional

from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class OptionsSkill(BaseSkillWrapper):
    """Wrapper for options Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "options"

    def calc_greeks(self, spot: float, strike: float, time: float,
                    rate: float, vol: float, option_type: str) -> Dict[str, float]:
        """Calculate all Greeks for an option.

        Note: greeks.py outputs text format. We parse the key values.
        """
        result = self._run("greeks",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --vol {vol} --type {option_type}",
                          output_format=SkillOutputFormat.RAW)

        return self._parse_greeks_output(result.output or "")

    def calc_bs_price(self, spot: float, strike: float, time: float,
                      rate: float, vol: float, option_type: str) -> float:
        """Calculate Black-Scholes theoretical price.

        Note: pricing.py outputs text format. We parse the price value.
        """
        result = self._run("pricing",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --vol {vol} --type {option_type}",
                          output_format=SkillOutputFormat.RAW)

        return self._parse_pricing_output(result.output or "")

    def calc_iv(self, spot: float, strike: float, time: float,
                rate: float, market_price: float, option_type: str) -> float:
        """Calculate implied volatility from market price.

        Note: iv.py supports --json flag.
        """
        result = self._run("iv",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --price {market_price} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)

        # iv.py returns JSON with implied_volatility key
        if isinstance(result.output, dict):
            return result.output.get("implied_volatility", 0.0) or 0.0
        return 0.0

    def _parse_greeks_output(self, output: str) -> Dict[str, float]:
        """Parse Greeks from text output.

        Example output format:
          Delta (Δ):      0.5500  (price change per $1 underlying)
          Gamma (Γ):    0.012345  (delta change per $1 underlying)
          Theta (Θ):     -0.0234  (daily time decay)
          Vega (ν):       0.1234  (price change per 1% vol)
          Rho (ρ):        0.0567  (price change per 1% rate)
        """
        greeks = {
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0
        }

        patterns = {
            "delta": r"Delta.*?:\s*([-\d.]+)",
            "gamma": r"Gamma.*?:\s*([-\d.]+)",
            "theta": r"Theta.*?:\s*([-\d.]+)",
            "vega": r"Vega.*?:\s*([-\d.]+)",
            "rho": r"Rho.*?:\s*([-\d.]+)"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    greeks[key] = float(match.group(1))
                except ValueError:
                    pass

        return greeks

    def _parse_pricing_output(self, output: str) -> float:
        """Parse price from pricing.py text output.

        Example output format:
          Price:       12.3456
        """
        match = re.search(r"Price:\s*([\d,.]+)", output, re.IGNORECASE)
        if match:
            try:
                # Remove commas from number
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass
        return 0.0
