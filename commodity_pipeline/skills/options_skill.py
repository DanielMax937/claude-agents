"""Wrapper for options skill (Greeks, IV, Black-Scholes pricing)."""
from typing import Dict

from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class OptionsSkill(BaseSkillWrapper):
    """Wrapper for options Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "options"

    def calc_greeks(self, spot: float, strike: float, time: float,
                    rate: float, vol: float, option_type: str) -> Dict[str, float]:
        """Calculate all Greeks for an option."""
        result = self._run("greeks",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --vol {vol} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)
        return result.output or {}

    def calc_bs_price(self, spot: float, strike: float, time: float,
                      rate: float, vol: float, option_type: str) -> float:
        """Calculate Black-Scholes theoretical price."""
        result = self._run("pricing",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --vol {vol} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)
        return (result.output or {}).get("price", 0.0)

    def calc_iv(self, spot: float, strike: float, time: float,
                rate: float, market_price: float, option_type: str) -> float:
        """Calculate implied volatility from market price."""
        result = self._run("iv",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --price {market_price} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)
        return (result.output or {}).get("iv", 0.0)
