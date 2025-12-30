# Position Review Mode Design

**Date:** 2025-12-30
**Author:** Claude + User
**Status:** Design Approved

## Overview

Add a **Review Mode** to the commodity pipeline that analyzes user's existing options holdings and generates hold/adjust/close recommendations with detailed metric explanations.

### Key Use Case

Instead of **discovering** which commodities to analyze (screening), users provide their existing options positions and the pipeline evaluates whether to hold, adjust, or close them based on:
- Greeks analysis (delta, gamma, theta, vega)
- Technical analysis of underlying commodity
- Time factors (DTE, decay rate)
- News sentiment

## Architecture

### Pipeline Flow Comparison

**Discovery Mode** (current):
```
Screening → Technical → Options → News → Alerts → Strategy
```

**Review Mode** (new):
```
Holdings → Extract Underlyings → Technical → Options → News → PositionReview → Report
```

### Key Differences in Review Mode

| Aspect | Discovery Mode | Review Mode |
|--------|----------------|-------------|
| Input | CLI args (top-n, workers) | Holdings JSON |
| Screening | ScreeningStage finds movers | Skip - underlyings from holdings |
| Alerts | Gmail alerts for commodities | Skip - we know what we hold |
| Strategy | Generates new trade ideas | Evaluates existing positions |

## Data Models

### Holdings Input Format

```json
[
    {
        "code": "CU2501-C-75000",
        "symbol": "CU",
        "expiry": "2025-01",
        "strike": 75000,
        "type": "call",
        "quantity": 2,
        "avg_cost": 1200,
        "open_date": "2024-12-01"
    }
]
```

### New Model: HoldingPosition

```python
@dataclass
class HoldingPosition:
    """Represents a user's options position."""
    code: str              # Full option identifier
    symbol: str            # Underlying commodity
    expiry: str            # Contract expiry
    strike: float          # Strike price
    type: OptionType       # CALL or PUT
    quantity: int          # Position size (+ long, - short)
    avg_cost: float        # Average entry price
    open_date: Optional[datetime] = None

    @property
    def current_pnl(self, current_price: float) -> float:
        """Calculate unrealized P/L."""

    @property
    def days_to_expiry(self) -> int:
        """Days until expiration."""

    @property
    def is_itm(self, spot: float) -> bool:
        """Whether position is in-the-money."""
```

### Signal Output Structure

```python
{
    "position_code": "CU2501-C-75000",
    "signal": "bullish",          # bullish | bearish | neutral
    "confidence": 0.75,           # 0-1
    "scores": {
        "greeks": 65,
        "technical": 80,
        "time": 70,
        "news": 85
    },
    "metrics": {
        "delta": 0.52,
        "gamma": 0.08,
        "theta": -12.3,
        "vega": 42.1,
        "iv_rank": 45,
        "spot": 74520,
        "dte": 45,
        "rsi": 58
    },
    "recommendation": "HOLD",     # HOLD | ADJUST | CLOSE
    "reason": "Detailed explanation of each metric..."
}
```

## Components

### 1. Option Code Parser (utils/parsers.py)

Parse Chinese futures options codes like "CU2501-C-75000":
- Symbol: CU
- Expiry: 2501 (January 2025)
- Type: C (Call) or P (Put)
- Strike: 75000

### 2. PositionReviewStage (stages/position_review.py)

**Responsibilities:**
- Fetch current market data for each holding
- Calculate position-level metrics
- Score each dimension (Greeks, Technical, Time, News)
- Generate weighted signal

**Scoring Logic:**

```python
def score_greeks(position, current_greeks, trend) -> int:
    score = 50  # baseline

    # Delta alignment with trend
    if trend == "bullish":
        if position.type == CALL and current_greeks.delta > 0.3:
            score += 20
        elif position.type == PUT:
            score -= 30

    # Theta urgency
    if position.days_to_expiry < 7:
        score -= 25  # last week burn
    elif position.days_to_expiry < 21:
        score -= 10  # decay zone

    # Gamma risk
    if abs(current_greeks.gamma) > 0.1:
        score -= 15  # high gamma risk

    return clamp(score, 0, 100)
```

### 3. CLI Integration

```python
parser.add_argument("--holdings", type=str,
    help="Path to holdings JSON file or JSON string for review mode")

parser.add_argument("--signal-weights", type=str,
    default="greeks:30,technical:30,time:20,news:20",
    help="Weights for signal scoring")
```

### 4. Output Format

**Terminal Output:**
```
╭─────────────────────────────────────────────────────────────────╮
│  POSITION REVIEW REPORT                     2025-12-30 21:15    │
╰─────────────────────────────────────────────────────────────────╯

│  CU2501-C-75000  (x2)  │  Cost: ¥1,200  │  Current: ¥1,450    │
│                         │  P/L: +¥500    │  DTE: 45 days       │
│  Spot: ¥74,520         │  ITM: +¥520    │  IV: 18.5%          │
├─────────────────────────────────────────────────────────────────┤
│  SIGNAL      │  BULLISH     │  Confidence: 75%                 │
├─────────────────────────────────────────────────────────────────┤
│  Greeks      │  65/100  │  Detailed breakdown...              │
│  Technical   │  80/100  │  Trend, S/R, RSI, MACD...            │
│  Time        │  70/100  │  DTE, decay phase, roll timing...    │
│  News        │  85/100  │  Sentiment, headlines, impact...     │
├─────────────────────────────────────────────────────────────────┤
│  RECOMMENDATION                                            HOLD │
│                                                                 │
│  SUMMARY: Comprehensive explanation with action items...        │
╰─────────────────────────────────────────────────────────────────╯
```

## File Structure

```
commodity_pipeline/
├── models.py              # UPDATE: add HoldingPosition
├── config.py              # UPDATE: add review_mode, signal_weights
├── pipeline.py            # UPDATE: add _run_review() method
│
├── stages/
│   ├── position_review.py # NEW: PositionReviewStage
│   └── ...
│
├── output/
│   ├── terminal.py        # UPDATE: add format_position_review()
│   ├── markdown.py        # UPDATE: add save_position_review()
│   └── ...
│
└── utils/
    └── parsers.py         # NEW: parse_option_code(), parse_holdings()
```

## Implementation Tasks

1. Add `HoldingPosition` dataclass to `models.py`
2. Create `utils/parsers.py` with option code parsing
3. Create `stages/position_review.py` with scoring logic
4. Update `pipeline.py` to support review mode
5. Update output classes for detailed review formatting
6. Add CLI arguments
7. Write tests for parsers and scoring logic
8. Integration test with sample holdings

## Testing

- Unit tests for option code parsing (edge cases)
- Mock holdings for scoring logic verification
- Integration test: holdings → full review → verify output format
