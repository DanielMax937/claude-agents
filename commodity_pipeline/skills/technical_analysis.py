"""Wrapper for technical-analysis skill."""
import tempfile
import os
import json
import re
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
        # Save OHLCV data to temp file
        csv_data = self._to_csv(ohlcv)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            # Use RAW format since the script outputs mixed content
            result = self._run("analyze",
                              args=f"{temp_path} --symbol {code} --output json",
                              output_format=SkillOutputFormat.RAW)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        # Parse JSON from the raw output (script prints progress messages before JSON)
        data = self._extract_json(result.output or "")

        # Extract signals from the result
        signals = data.get("signals", {})
        patterns = data.get("patterns", {})

        # Determine overall trend from signal strength
        strength = signals.get("strength", 0)
        if strength > 30:
            overall_trend = TrendDirection.BULLISH
        elif strength < -30:
            overall_trend = TrendDirection.BEARISH
        else:
            overall_trend = TrendDirection.NEUTRAL

        # Get MA alignment
        ma_alignment = patterns.get("ma_alignment", {})
        ma_signal = ma_alignment.get("alignment", "neutral")

        # Get MACD signal
        macd_signals = patterns.get("macd_signals", {})
        macd_signal = macd_signals.get("signal", "neutral")

        # Get RSI
        rsi_signals = patterns.get("rsi_signals", {})
        rsi_value = rsi_signals.get("RSI", 50)
        rsi_signal = rsi_signals.get("signal", "neutral")

        # Get Bollinger position
        boll_squeeze = patterns.get("bollinger_squeeze", {})
        boll_position = boll_squeeze.get("position", "middle")

        # Get latest data for ATR
        latest = data.get("latest_data", {})
        atr_value = latest.get("ATR", 0)

        return TechnicalSignals(
            commodity_code=code,
            ma_signal=ma_signal,
            macd_signal=macd_signal,
            rsi_value=float(rsi_value) if rsi_value else 50.0,
            rsi_signal=rsi_signal,
            boll_position=boll_position,
            kdj_signal="neutral",  # Not directly available
            atr_value=float(atr_value) if atr_value else 0.0,
            obv_trend="flat",  # Not directly available
            cci_signal="neutral",  # Not directly available
            overall_trend=overall_trend,
            strength=int(signals.get("strength", 0))
        )

    def _extract_json(self, output: str) -> dict:
        """Extract JSON object from mixed output containing progress messages.

        The analyze.py script prints progress messages before the JSON output.
        This method finds and parses the JSON portion.
        """
        if not output:
            return {}

        # Try to find JSON object starting with {
        # Look for the first { that starts a valid JSON object
        for i, char in enumerate(output):
            if char == '{':
                try:
                    # Try to parse from this position
                    return json.loads(output[i:])
                except json.JSONDecodeError:
                    continue

        # If no valid JSON found, return empty dict
        return {}

    def _to_csv(self, ohlcv: List[OHLCVBar]) -> str:
        """Convert OHLCV bars to CSV format for skill input."""
        lines = ["date,open,high,low,close,volume"]
        for bar in ohlcv:
            lines.append(f"{bar.date},{bar.open},{bar.high},{bar.low},{bar.close},{bar.volume}")
        return "\n".join(lines)
