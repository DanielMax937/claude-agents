"""Wrapper for china-futures skill."""
from typing import List, Dict, Any
from datetime import datetime

from commodity_pipeline.models import Commodity, OHLCVBar
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class ChinaFuturesSkill(BaseSkillWrapper):
    """Wrapper for china-futures Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "china-futures"

    def get_main_contracts(self) -> List[Commodity]:
        """Get all main contracts for commodities with price changes."""
        # Use futures_quote with --main --json flags, longer timeout
        result = self._run("futures_quote", args="--main --json",
                          output_format=SkillOutputFormat.JSON, timeout=300)
        commodities = []
        for c in result.output or []:
            commodities.append(Commodity(
                code=c.get("code", c.get("symbol", "").rstrip("0")),
                name=c.get("name", ""),
                exchange=c.get("exchange", ""),
                main_contract=c.get("symbol", ""),
                price=float(c.get("price", 0) or 0),
                change_1d=float(c.get("change_1d", c.get("pct_change", 0)) or 0),
                change_3d=float(c.get("change_3d", 0) or 0),
                change_5d=float(c.get("change_5d", 0) or 0)
            ))
        return commodities

    def get_ohlcv(self, contract: str, days: int = 15) -> List[OHLCVBar]:
        """Get OHLCV data for a contract."""
        result = self._run("futures_history",
                          args=f"--contract {contract} --days {days} --json",
                          output_format=SkillOutputFormat.JSON)

        bars = []
        for bar in result.output or []:
            bar_date = bar.get("date", "")
            if isinstance(bar_date, str):
                bar_date = datetime.strptime(bar_date[:10], "%Y-%m-%d").date()

            bars.append(OHLCVBar(
                date=bar_date,
                open=float(bar.get("open", 0)),
                high=float(bar.get("high", 0)),
                low=float(bar.get("low", 0)),
                close=float(bar.get("close", 0)),
                volume=int(bar.get("volume", 0))
            ))
        return bars

    def get_options_chain(self, underlying: str) -> List[Dict[str, Any]]:
        """Get options chain for a commodity."""
        result = self._run("options_chain",
                          args=f"--underlying {underlying} --json",
                          output_format=SkillOutputFormat.JSON)
        return result.output or []
