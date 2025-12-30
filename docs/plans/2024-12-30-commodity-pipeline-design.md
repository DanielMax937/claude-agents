# Commodity Analysis Pipeline - Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an on-demand commodity analysis pipeline that screens top movers, performs technical analysis, evaluates options, gathers news, and recommends trading strategies.

**Architecture:** Modular pipeline with independent stages. Stage-level parallelization via asyncio, item-level parallelization via ThreadPoolExecutor.

**Tech Stack:** Python 3.11+, asyncio, ThreadPoolExecutor, SkillWrapper (existing), dataclasses

---

## Decisions Made

| Decision | Choice |
|----------|--------|
| Use case | On-demand analysis (run manually) |
| Output formats | Terminal + Markdown + JSON |
| News sources | Multiple Chinese sites (East Money, Sina, etc.) |
| Technical indicators | Comprehensive (MA, MACD, RSI, BOLL, KDJ, ATR, OBV, CCI) |
| Strategy types | All (directional, volatility, income) |
| Error handling | Fail fast |
| Architecture | Modular pipeline with stages |
| Parallelization | Stage-level (asyncio) + Item-level (ThreadPool, 8 workers) |

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: SCREENING (Sequential)                                        │
│  Steps 1-4: Get contracts → Calc changes → Filter top movers            │
│  Output: List[Commodity]                                                │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: DATA GATHERING (Parallel via asyncio.gather)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Technical   │  │ Options     │  │ News        │  │ Gmail       │     │
│  │ Steps 5-6   │  │ Step 7      │  │ Step 8      │  │ Step 9      │     │
│  │ ThreadPool  │  │ ThreadPool  │  │ ThreadPool  │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: STRATEGY (Sequential)                                         │
│  Step 10: Synthesize all data → Generate 3+ recommendations             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: OUTPUT                                                        │
│  Terminal + Markdown + JSON                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
commodity_pipeline/
├── __init__.py
├── config.py                   # PipelineConfig dataclass
├── models.py                   # Commodity, TechnicalSignals, OptionContract, etc.
├── logger.py                   # PipelineLogger with step tracking
│
├── stages/
│   ├── __init__.py
│   ├── screening.py            # Steps 1-4
│   ├── technical.py            # Steps 5-6
│   ├── options.py              # Step 7
│   ├── news.py                 # Step 8
│   ├── alerts.py               # Step 9
│   └── strategy.py             # Step 10
│
├── skills/
│   ├── __init__.py
│   ├── china_futures.py
│   ├── technical_analysis.py
│   ├── options_skill.py
│   ├── scraper.py
│   └── gmail.py
│
├── output/
│   ├── __init__.py
│   ├── terminal.py
│   ├── markdown.py
│   └── json_export.py
│
└── run.py                      # CLI entry point
```

---

## Data Models

```python
@dataclass
class Commodity:
    code: str                    # e.g., "rb2501"
    name: str                    # e.g., "螺纹钢"
    exchange: str                # e.g., "SHFE"
    main_contract: str
    price: float
    change_1d: float
    change_3d: float
    change_5d: float

@dataclass
class OHLCVBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class TechnicalSignals:
    commodity_code: str
    ma_signal: str
    macd_signal: str
    rsi_value: float
    rsi_signal: str
    boll_position: str
    kdj_signal: str
    atr_value: float
    obv_trend: str
    cci_signal: str
    overall_trend: TrendDirection
    strength: int                # 1-10

@dataclass
class OptionContract:
    code: str
    underlying: str
    strike: float
    expiry: date
    option_type: str             # "call" | "put"
    market_price: float
    volume: int
    iv: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    bs_value: float
    mispricing: float

@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    published: date
    summary: Optional[str] = None
    sentiment: Optional[str] = None

@dataclass
class StrategyRecommendation:
    name: str                    # e.g., "Bull Call Spread"
    type: str                    # "directional" | "volatility" | "income"
    legs: list
    max_profit: float
    max_loss: float
    breakeven: list[float]
    rationale: str
    confidence: int              # 1-10
```

---

## Configuration

```python
@dataclass
class PipelineConfig:
    max_workers: int = 8
    top_n_movers: int = 3
    periods: list[int] = (1, 3, 5)
    ohlcv_days: int = 15
    indicators: list[str] = ("ma", "macd", "rsi", "boll", "kdj", "atr", "obv", "cci")
    top_options_by_volume: int = 5
    risk_free_rate: float = 0.02
    news_sources: list[str] = ("eastmoney", "sina")
    max_news_per_source: int = 5
    output_dir: str = "reports"
```

---

## Skill Integration

Each skill gets a wrapper class that:
- Uses existing `SkillWrapper` / `run_skill()` from this project
- Returns strongly-typed data models
- Fails fast with clear error messages

Skills used:
- `china-futures` - Main contracts, price data, options chain
- `technical-analysis` - TA indicators
- `options` - Greeks, IV, Black-Scholes pricing
- `scraper` - News from East Money, Sina
- `gmail` - Gmail alerts

---

## Logging

- **Terminal**: Real-time step progress with timestamps
- **Log file**: Full debug details (`reports/YYYYMMDD_HHMMSS_pipeline.log`)
- **JSON log**: Structured per-step results (`reports/YYYYMMDD_HHMMSS_pipeline.jsonl`)

---

## CLI Usage

```bash
# Run full pipeline with defaults
uv run python -m commodity_pipeline.run

# Customize settings
uv run python -m commodity_pipeline.run --workers 4 --top 5 --output ./my_reports
```

---

## Output Files

```
reports/
├── 2024-12-30-commodity-analysis.md    # Human-readable report
├── 2024-12-30-commodity-analysis.json  # Machine-readable data
├── 20241230_173001_pipeline.log        # Execution log
└── 20241230_173001_pipeline.jsonl      # Structured step data
```
