"""Pipeline configuration."""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class PipelineConfig:
    """Configuration for the commodity analysis pipeline."""

    # Thread pool settings
    max_workers: int = 8              # Concurrent threads per stage

    # Screening settings
    top_n_movers: int = 3             # Top N gainers/losers per period
    periods: Tuple[int, ...] = (1, 3, 5)  # Days to check: 1d, 3d, 5d

    # Technical analysis settings
    ohlcv_days: int = 15              # Days of history
    indicators: Tuple[str, ...] = (
        "ma", "macd", "rsi", "boll", "kdj", "atr", "obv", "cci"
    )

    # Options settings
    top_options_by_volume: int = 5    # Top N options per commodity
    risk_free_rate: float = 0.02      # For BS pricing

    # News settings
    news_sources: Tuple[str, ...] = ("eastmoney", "sina")
    max_news_per_source: int = 5

    # Output settings
    output_dir: str = "reports"
