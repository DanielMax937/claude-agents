"""Data models for the commodity analysis pipeline."""
from dataclasses import dataclass
from datetime import date
from typing import Optional
from enum import Enum


class TrendDirection(Enum):
    """Overall trend direction from technical analysis."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class Commodity:
    """A commodity with its main contract info and price changes."""
    code: str                    # e.g., "rb2501" (螺纹钢)
    name: str                    # e.g., "螺纹钢"
    exchange: str                # e.g., "SHFE"
    main_contract: str           # e.g., "rb2501"
    price: float                 # Current price
    change_1d: float             # % change today
    change_3d: float             # % change last 3 days
    change_5d: float             # % change last 5 days


@dataclass
class OHLCVBar:
    """Single OHLCV bar for one trading day."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class TechnicalSignals:
    """Technical analysis results for a commodity."""
    commodity_code: str
    ma_signal: str               # "buy" | "sell" | "neutral"
    macd_signal: str
    rsi_value: float
    rsi_signal: str
    boll_position: str           # "above_upper" | "middle" | "below_lower"
    kdj_signal: str
    atr_value: float
    obv_trend: str               # "up" | "down" | "flat"
    cci_signal: str
    overall_trend: TrendDirection
    strength: int                # 1-10 score
