"""Wrapper for technical-analysis skill."""
from typing import List, Tuple

from commodity_pipeline.models import TechnicalSignals, OHLCVBar, TrendDirection
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class TechnicalAnalysisSkill(BaseSkillWrapper):
    """Wrapper for technical-analysis Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "technical-analysis"

    def analyze(self, code: str, ohlcv: List[OHLCVBar],
                indicators: Tuple[str, ...] = ("ma", "macd", "rsi", "boll", "kdj", "atr", "obv", "cci")
               ) -> TechnicalSignals:
        """Run comprehensive technical analysis on OHLCV data."""
        csv_data = self._to_csv(ohlcv)
        indicators_str = ",".join(indicators)

        result = self._run("analyze",
                          args=f"--data '{csv_data}' --indicators {indicators_str} --json",
                          output_format=SkillOutputFormat.JSON)

        data = result.output or {}

        # Map string trend to enum
        trend_map = {
            "bullish": TrendDirection.BULLISH,
            "bearish": TrendDirection.BEARISH,
            "neutral": TrendDirection.NEUTRAL
        }
        overall_trend = trend_map.get(
            data.get("overall_trend", "neutral").lower(),
            TrendDirection.NEUTRAL
        )

        return TechnicalSignals(
            commodity_code=code,
            ma_signal=data.get("ma_signal", "neutral"),
            macd_signal=data.get("macd_signal", "neutral"),
            rsi_value=float(data.get("rsi_value", 50)),
            rsi_signal=data.get("rsi_signal", "neutral"),
            boll_position=data.get("boll_position", "middle"),
            kdj_signal=data.get("kdj_signal", "neutral"),
            atr_value=float(data.get("atr_value", 0)),
            obv_trend=data.get("obv_trend", "flat"),
            cci_signal=data.get("cci_signal", "neutral"),
            overall_trend=overall_trend,
            strength=int(data.get("strength", 5))
        )

    def _to_csv(self, ohlcv: List[OHLCVBar]) -> str:
        """Convert OHLCV bars to CSV format for skill input."""
        lines = ["date,open,high,low,close,volume"]
        for bar in ohlcv:
            lines.append(f"{bar.date},{bar.open},{bar.high},{bar.low},{bar.close},{bar.volume}")
        return "\\n".join(lines)
