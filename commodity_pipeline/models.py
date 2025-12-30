"""Data models for the commodity analysis pipeline."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from enum import Enum


class TrendDirection(Enum):
    """Overall trend direction from technical analysis."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class OptionType(Enum):
    """Option type enumeration."""
    CALL = "call"
    PUT = "put"


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


@dataclass
class OptionContract:
    """Single option contract with Greeks and valuation."""
    code: str                    # Option code
    underlying: str              # Underlying commodity
    strike: float
    expiry: date
    option_type: str             # "call" | "put"
    market_price: float
    volume: int
    iv: float                    # Implied volatility
    # Greeks
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    # Calculated
    bs_value: float              # Black-Scholes theoretical value
    mispricing: float            # market_price - bs_value


@dataclass
class NewsItem:
    """A news article from financial sources."""
    title: str
    source: str                  # "eastmoney" | "sina" | "gmail"
    url: str
    published: date
    summary: Optional[str] = None
    sentiment: Optional[str] = None  # "positive" | "negative" | "neutral"


@dataclass
class StrategyRecommendation:
    """A recommended options trading strategy."""
    name: str                    # e.g., "Bull Call Spread"
    type: str                    # "directional" | "volatility" | "income"
    legs: list                   # List of option legs to trade
    max_profit: float
    max_loss: float
    breakeven: list              # List of breakeven prices
    rationale: str               # Why this strategy
    confidence: int              # 1-10


@dataclass
class HoldingPosition:
    """Represents a user's options position for review."""
    code: str                      # Full option identifier e.g., "CU2501-C-75000"
    symbol: str                    # Underlying commodity e.g., "CU"
    expiry: str                    # Contract expiry e.g., "2025-01" or "2025-01-15"
    strike: float                  # Strike price
    type: OptionType               # CALL or PUT
    quantity: int                  # Position size (+ for long, - for short)
    avg_cost: float                # Average entry price per contract
    open_date: Optional[date] = None  # When position was opened

    def current_pnl(self, current_price: float) -> float:
        """Calculate unrealized P/L at current market price."""
        return (current_price - self.avg_cost) * self.quantity

    @property
    def days_to_expiry(self) -> int:
        """Calculate days until expiration."""
        today = date.today()

        # Parse expiry - handle both "YYYY-MM" and "YYYY-MM-DD" formats
        if "-" in self.expiry:
            parts = self.expiry.split("-")
            if len(parts) == 2:
                # YYYY-MM format - use last day of month
                year, month = int(parts[0]), int(parts[1])
                if month == 12:
                    expiry_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    expiry_date = date(year, month + 1, 1) - timedelta(days=1)
            else:
                # YYYY-MM-DD format
                expiry_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            # Fallback - assume end of current year
            expiry_date = date(today.year + 1, 1, 1) - timedelta(days=1)

        return (expiry_date - today).days

    def is_itm(self, spot: float) -> bool:
        """Check if position is in-the-money."""
        if self.type == OptionType.CALL:
            return spot > self.strike
        else:  # PUT
            return spot < self.strike
