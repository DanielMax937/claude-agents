"""Pipeline configuration."""
from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional, Any


@dataclass
class PipelineConfig:
    """Configuration for the commodity analysis pipeline."""

    # Pipeline mode
    mode: str = "discovery"            # "discovery" | "review"
    holdings: Optional[List[Dict[str, Any]]] = None  # User's holdings for review mode

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

    # Review mode settings
    signal_weights: Dict[str, int] = field(default_factory=lambda: {
        "greeks": 30,
        "technical": 30,
        "time": 20,
        "news": 20
    })

    # Output settings
    output_dir: str = "reports"
