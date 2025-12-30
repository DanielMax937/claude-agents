# Commodity Analysis Pipeline - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an on-demand commodity analysis pipeline that screens top movers, performs technical analysis, evaluates options, gathers news, and recommends trading strategies.

**Architecture:** Modular pipeline with independent stages. Stage-level parallelization via asyncio.gather(), item-level parallelization via ThreadPoolExecutor(max_workers=8). Each stage has its own module, skill wrappers abstract Claude Code skill calls.

**Tech Stack:** Python 3.11+, asyncio, concurrent.futures, dataclasses, existing SkillWrapper

---

## Phase 1: Project Foundation

### Task 1: Create Package Structure

**Files:**
- Create: `commodity_pipeline/__init__.py`
- Create: `commodity_pipeline/stages/__init__.py`
- Create: `commodity_pipeline/skills/__init__.py`
- Create: `commodity_pipeline/output/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

**Step 1: Create directory structure**

```bash
mkdir -p commodity_pipeline/stages commodity_pipeline/skills commodity_pipeline/output tests
```

**Step 2: Create package init files**

```python
# commodity_pipeline/__init__.py
"""Commodity Analysis Pipeline - On-demand market analysis and strategy recommendations."""
__version__ = "0.1.0"
```

```python
# commodity_pipeline/stages/__init__.py
"""Pipeline stages for data gathering and analysis."""
```

```python
# commodity_pipeline/skills/__init__.py
"""Skill wrappers for Claude Code skills integration."""
```

```python
# commodity_pipeline/output/__init__.py
"""Output formatters for terminal, markdown, and JSON."""
```

```python
# tests/__init__.py
"""Tests for commodity pipeline."""
```

**Step 3: Commit**

```bash
git add commodity_pipeline/ tests/
git commit -m "feat: create commodity_pipeline package structure"
```

---

### Task 2: Create Data Models - Enums and Base Types

**Files:**
- Create: `commodity_pipeline/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
"""Tests for data models."""
import pytest
from datetime import date


def test_trend_direction_enum_values():
    """TrendDirection enum should have bullish, bearish, neutral values."""
    from commodity_pipeline.models import TrendDirection

    assert TrendDirection.BULLISH.value == "bullish"
    assert TrendDirection.BEARISH.value == "bearish"
    assert TrendDirection.NEUTRAL.value == "neutral"


def test_commodity_dataclass_creation():
    """Commodity dataclass should be creatable with required fields."""
    from commodity_pipeline.models import Commodity

    c = Commodity(
        code="rb2501",
        name="螺纹钢",
        exchange="SHFE",
        main_contract="rb2501",
        price=3500.0,
        change_1d=1.5,
        change_3d=2.3,
        change_5d=-0.8
    )

    assert c.code == "rb2501"
    assert c.name == "螺纹钢"
    assert c.price == 3500.0
    assert c.change_1d == 1.5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'commodity_pipeline.models'"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/models.py
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/models.py tests/test_models.py
git commit -m "feat: add TrendDirection enum and Commodity dataclass"
```

---

### Task 3: Create Data Models - OHLCVBar and TechnicalSignals

**Files:**
- Modify: `commodity_pipeline/models.py`
- Modify: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py (append)
def test_ohlcv_bar_creation():
    """OHLCVBar should store OHLCV data for a single day."""
    from commodity_pipeline.models import OHLCVBar

    bar = OHLCVBar(
        date=date(2024, 12, 30),
        open=3500.0,
        high=3550.0,
        low=3480.0,
        close=3520.0,
        volume=100000
    )

    assert bar.date == date(2024, 12, 30)
    assert bar.high == 3550.0
    assert bar.volume == 100000


def test_technical_signals_creation():
    """TechnicalSignals should store all indicator results."""
    from commodity_pipeline.models import TechnicalSignals, TrendDirection

    signals = TechnicalSignals(
        commodity_code="rb2501",
        ma_signal="buy",
        macd_signal="buy",
        rsi_value=65.0,
        rsi_signal="neutral",
        boll_position="middle",
        kdj_signal="buy",
        atr_value=50.0,
        obv_trend="up",
        cci_signal="neutral",
        overall_trend=TrendDirection.BULLISH,
        strength=7
    )

    assert signals.commodity_code == "rb2501"
    assert signals.overall_trend == TrendDirection.BULLISH
    assert signals.strength == 7
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_ohlcv_bar_creation -v`
Expected: FAIL with "cannot import name 'OHLCVBar'"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/models.py (append after Commodity)

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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add commodity_pipeline/models.py tests/test_models.py
git commit -m "feat: add OHLCVBar and TechnicalSignals dataclasses"
```

---

### Task 4: Create Data Models - OptionContract

**Files:**
- Modify: `commodity_pipeline/models.py`
- Modify: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py (append)
def test_option_contract_creation():
    """OptionContract should store option data with Greeks."""
    from commodity_pipeline.models import OptionContract

    opt = OptionContract(
        code="rb2501-C-3600",
        underlying="rb2501",
        strike=3600.0,
        expiry=date(2025, 1, 15),
        option_type="call",
        market_price=50.0,
        volume=1000,
        iv=0.25,
        delta=0.45,
        gamma=0.02,
        theta=-5.0,
        vega=10.0,
        rho=0.5,
        bs_value=48.0,
        mispricing=2.0
    )

    assert opt.code == "rb2501-C-3600"
    assert opt.option_type == "call"
    assert opt.iv == 0.25
    assert opt.delta == 0.45
    assert opt.mispricing == 2.0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_option_contract_creation -v`
Expected: FAIL with "cannot import name 'OptionContract'"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/models.py (append)

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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add commodity_pipeline/models.py tests/test_models.py
git commit -m "feat: add OptionContract dataclass with Greeks"
```

---

### Task 5: Create Data Models - NewsItem and StrategyRecommendation

**Files:**
- Modify: `commodity_pipeline/models.py`
- Modify: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py (append)
def test_news_item_creation():
    """NewsItem should store news article info."""
    from commodity_pipeline.models import NewsItem

    news = NewsItem(
        title="螺纹钢期货大涨",
        source="eastmoney",
        url="https://example.com/news/1",
        published=date(2024, 12, 30),
        summary="市场看涨情绪浓厚",
        sentiment="positive"
    )

    assert news.title == "螺纹钢期货大涨"
    assert news.sentiment == "positive"


def test_news_item_optional_fields():
    """NewsItem should allow optional summary and sentiment."""
    from commodity_pipeline.models import NewsItem

    news = NewsItem(
        title="Test",
        source="sina",
        url="https://example.com",
        published=date(2024, 12, 30)
    )

    assert news.summary is None
    assert news.sentiment is None


def test_strategy_recommendation_creation():
    """StrategyRecommendation should store strategy details."""
    from commodity_pipeline.models import StrategyRecommendation

    strat = StrategyRecommendation(
        name="Bull Call Spread",
        type="directional",
        legs=[
            {"action": "buy", "code": "rb2501-C-3500", "qty": 1},
            {"action": "sell", "code": "rb2501-C-3600", "qty": 1}
        ],
        max_profit=5000.0,
        max_loss=1000.0,
        breakeven=[3550.0],
        rationale="Technical signals bullish, IV low",
        confidence=7
    )

    assert strat.name == "Bull Call Spread"
    assert strat.type == "directional"
    assert len(strat.legs) == 2
    assert strat.confidence == 7
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_news_item_creation -v`
Expected: FAIL with "cannot import name 'NewsItem'"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/models.py (append)

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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS (all 8 tests)

**Step 5: Commit**

```bash
git add commodity_pipeline/models.py tests/test_models.py
git commit -m "feat: add NewsItem and StrategyRecommendation dataclasses"
```

---

### Task 6: Create Configuration

**Files:**
- Create: `commodity_pipeline/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
"""Tests for pipeline configuration."""
import pytest


def test_pipeline_config_defaults():
    """PipelineConfig should have sensible defaults."""
    from commodity_pipeline.config import PipelineConfig

    config = PipelineConfig()

    assert config.max_workers == 8
    assert config.top_n_movers == 3
    assert config.periods == (1, 3, 5)
    assert config.ohlcv_days == 15
    assert config.top_options_by_volume == 5
    assert config.risk_free_rate == 0.02
    assert config.output_dir == "reports"


def test_pipeline_config_custom_values():
    """PipelineConfig should accept custom values."""
    from commodity_pipeline.config import PipelineConfig

    config = PipelineConfig(
        max_workers=4,
        top_n_movers=5,
        output_dir="./my_reports"
    )

    assert config.max_workers == 4
    assert config.top_n_movers == 5
    assert config.output_dir == "./my_reports"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/config.py
"""Pipeline configuration."""
from dataclasses import dataclass, field
from typing import Tuple, List


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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/config.py tests/test_config.py
git commit -m "feat: add PipelineConfig with defaults"
```

---

### Task 7: Create Logger - Basic Setup

**Files:**
- Create: `commodity_pipeline/logger.py`
- Create: `tests/test_logger.py`

**Step 1: Write the failing test**

```python
# tests/test_logger.py
"""Tests for pipeline logger."""
import pytest
import tempfile
import os


def test_pipeline_logger_creates_log_files():
    """PipelineLogger should create log files in output directory."""
    from commodity_pipeline.logger import PipelineLogger

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = PipelineLogger(output_dir=tmpdir)

        # Log file should exist
        assert logger.log_file.exists()
        assert logger.json_log_file.exists()

        # Files should be in the output dir
        assert str(tmpdir) in str(logger.log_file)


def test_pipeline_logger_step_start():
    """PipelineLogger should log step start."""
    from commodity_pipeline.logger import PipelineLogger

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = PipelineLogger(output_dir=tmpdir)
        logger.step_start(1, "Get main contracts", "Fetching from API")

        # Check JSON log has entry
        with open(logger.json_log_file) as f:
            content = f.read()
            assert '"event": "step_start"' in content
            assert '"step": 1' in content
            assert "Get main contracts" in content
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_logger.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/logger.py
"""Structured logging for pipeline execution."""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import asdict, is_dataclass


class PipelineLogger:
    """Structured logger for pipeline execution with JSON logging."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create log files for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"{timestamp}_pipeline.log"
        self.json_log_file = self.output_dir / f"{timestamp}_pipeline.jsonl"

        # Touch files to create them
        self.log_file.touch()
        self.json_log_file.touch()

        # Setup console + file logging
        self.logger = logging.getLogger(f"commodity_pipeline_{timestamp}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Clear any existing handlers

        # Console handler (INFO level)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-5s | %(message)s",
            datefmt="%H:%M:%S"
        ))

        # File handler (DEBUG level)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        ))

        self.logger.addHandler(console)
        self.logger.addHandler(file_handler)

    def step_start(self, step: int, name: str, details: str = ""):
        """Log step start."""
        self.logger.info(f"Step {step} START | {name} | {details}")
        self._write_json_log("step_start", step=step, name=name, details=details)

    def step_complete(self, step: int, name: str, result_summary: str, data: Any = None):
        """Log step completion with result."""
        self.logger.info(f"Step {step} DONE  | {name} | {result_summary}")

        # Convert dataclass to dict for JSON
        if data is not None:
            if is_dataclass(data) and not isinstance(data, type):
                data = asdict(data)
            elif isinstance(data, list) and len(data) > 0:
                if is_dataclass(data[0]) and not isinstance(data[0], type):
                    data = [asdict(d) for d in data]

        self._write_json_log("step_complete", step=step, name=name,
                            summary=result_summary, data=data)

    def step_error(self, step: int, name: str, error: str):
        """Log step failure."""
        self.logger.error(f"Step {step} FAIL  | {name} | {error}")
        self._write_json_log("step_error", step=step, name=name, error=error)

    def item_progress(self, step: int, current: int, total: int, item: str):
        """Log progress within a step."""
        self.logger.debug(f"Step {step} | [{current}/{total}] | {item}")

    def _write_json_log(self, event_type: str, **data):
        """Write structured JSON log line."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data
        }
        with open(self.json_log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module."""
    return logging.getLogger(f"commodity_pipeline.{name}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_logger.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/logger.py tests/test_logger.py
git commit -m "feat: add PipelineLogger with JSON logging"
```

---

## Phase 2: Skill Wrappers

### Task 8: Create Base Skill Wrapper Pattern

**Files:**
- Create: `commodity_pipeline/skills/base.py`
- Create: `tests/test_skills_base.py`

**Step 1: Write the failing test**

```python
# tests/test_skills_base.py
"""Tests for skill wrapper base."""
import pytest


def test_skill_error_creation():
    """SkillError should store skill name and error message."""
    from commodity_pipeline.skills.base import SkillError

    err = SkillError("china-futures", "Network timeout")

    assert err.skill_name == "china-futures"
    assert err.message == "Network timeout"
    assert "china-futures" in str(err)
    assert "Network timeout" in str(err)


def test_base_skill_wrapper_abstract():
    """BaseSkillWrapper should be abstract and require skill_name."""
    from commodity_pipeline.skills.base import BaseSkillWrapper

    # Should not be instantiable directly
    with pytest.raises(TypeError):
        BaseSkillWrapper()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_base.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/skills/base.py
"""Base classes for skill wrappers."""
from abc import ABC, abstractmethod
from typing import Any
import sys
sys.path.insert(0, '.')  # Ensure we can import from project root
from skill_wrapper import run_skill, SkillOutputFormat, SkillResult


class SkillError(Exception):
    """Error raised when a skill execution fails."""

    def __init__(self, skill_name: str, message: str):
        self.skill_name = skill_name
        self.message = message
        super().__init__(f"Skill '{skill_name}' failed: {message}")


class BaseSkillWrapper(ABC):
    """Abstract base class for skill wrappers."""

    @property
    @abstractmethod
    def skill_name(self) -> str:
        """The name of the Claude Code skill."""
        pass

    def _run(self, script_name: str, args: str = "",
             output_format: SkillOutputFormat = SkillOutputFormat.JSON) -> SkillResult:
        """Run a skill script and return the result."""
        result = run_skill(self.skill_name, script_name, args=args,
                          output_format=output_format)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Unknown error")
        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills_base.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/skills/base.py tests/test_skills_base.py
git commit -m "feat: add BaseSkillWrapper and SkillError"
```

---

### Task 9: Create China Futures Skill Wrapper

**Files:**
- Create: `commodity_pipeline/skills/china_futures.py`
- Create: `tests/test_skills_china_futures.py`

**Step 1: Write the failing test**

```python
# tests/test_skills_china_futures.py
"""Tests for China Futures skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock


def test_china_futures_skill_name():
    """ChinaFuturesSkill should have correct skill name."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill

    skill = ChinaFuturesSkill()
    assert skill.skill_name == "china-futures"


def test_china_futures_get_main_contracts_parses_result():
    """get_main_contracts should parse JSON into Commodity objects."""
    from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
    from commodity_pipeline.models import Commodity

    # Mock the skill result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.parsed_output = [
        {
            "code": "rb2501",
            "name": "螺纹钢",
            "exchange": "SHFE",
            "main_contract": "rb2501",
            "price": 3500.0,
            "change_1d": 1.5,
            "change_3d": 2.0,
            "change_5d": -0.5
        }
    ]

    with patch('commodity_pipeline.skills.china_futures.run_skill', return_value=mock_result):
        skill = ChinaFuturesSkill()
        commodities = skill.get_main_contracts()

        assert len(commodities) == 1
        assert isinstance(commodities[0], Commodity)
        assert commodities[0].code == "rb2501"
        assert commodities[0].price == 3500.0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_china_futures.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/skills/china_futures.py
"""Wrapper for china-futures skill."""
from typing import List, Dict, Any
import sys
sys.path.insert(0, '.')
from skill_wrapper import run_skill, SkillOutputFormat
from commodity_pipeline.models import Commodity, OHLCVBar
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from datetime import datetime


class ChinaFuturesSkill(BaseSkillWrapper):
    """Wrapper for china-futures Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "china-futures"

    def get_main_contracts(self) -> List[Commodity]:
        """Step 1: Get all main contracts for commodities."""
        result = run_skill(self.skill_name, "main-contracts",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Failed to get main contracts")

        commodities = []
        for c in result.parsed_output or []:
            commodities.append(Commodity(
                code=c.get("code", ""),
                name=c.get("name", ""),
                exchange=c.get("exchange", ""),
                main_contract=c.get("main_contract", ""),
                price=float(c.get("price", 0)),
                change_1d=float(c.get("change_1d", 0)),
                change_3d=float(c.get("change_3d", 0)),
                change_5d=float(c.get("change_5d", 0))
            ))
        return commodities

    def get_ohlcv(self, contract: str, days: int = 15) -> List[OHLCVBar]:
        """Step 5: Get OHLCV data for a contract."""
        result = run_skill(self.skill_name, "history",
                          args=f"--contract {contract} --days {days}",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or f"Failed to get OHLCV for {contract}")

        bars = []
        for bar in result.parsed_output or []:
            bars.append(OHLCVBar(
                date=datetime.strptime(bar.get("date", ""), "%Y-%m-%d").date()
                     if isinstance(bar.get("date"), str) else bar.get("date"),
                open=float(bar.get("open", 0)),
                high=float(bar.get("high", 0)),
                low=float(bar.get("low", 0)),
                close=float(bar.get("close", 0)),
                volume=int(bar.get("volume", 0))
            ))
        return bars

    def get_options_chain(self, underlying: str) -> List[Dict[str, Any]]:
        """Step 7: Get options chain for a commodity."""
        result = run_skill(self.skill_name, "options",
                          args=f"--underlying {underlying}",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or f"Failed to get options for {underlying}")

        return result.parsed_output or []
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills_china_futures.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/skills/china_futures.py tests/test_skills_china_futures.py
git commit -m "feat: add ChinaFuturesSkill wrapper"
```

---

### Task 10: Create Options Skill Wrapper

**Files:**
- Create: `commodity_pipeline/skills/options_skill.py`
- Create: `tests/test_skills_options.py`

**Step 1: Write the failing test**

```python
# tests/test_skills_options.py
"""Tests for Options skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock


def test_options_skill_name():
    """OptionsSkill should have correct skill name."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    skill = OptionsSkill()
    assert skill.skill_name == "options"


def test_options_skill_calc_greeks():
    """calc_greeks should return Greeks dictionary."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.parsed_output = {
        "delta": 0.45,
        "gamma": 0.02,
        "theta": -5.0,
        "vega": 10.0,
        "rho": 0.5
    }

    with patch('commodity_pipeline.skills.options_skill.run_skill', return_value=mock_result):
        skill = OptionsSkill()
        greeks = skill.calc_greeks(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, vol=0.25, option_type="call"
        )

        assert greeks["delta"] == 0.45
        assert greeks["gamma"] == 0.02


def test_options_skill_calc_bs_price():
    """calc_bs_price should return Black-Scholes price."""
    from commodity_pipeline.skills.options_skill import OptionsSkill

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.parsed_output = {"price": 48.5}

    with patch('commodity_pipeline.skills.options_skill.run_skill', return_value=mock_result):
        skill = OptionsSkill()
        price = skill.calc_bs_price(
            spot=3500, strike=3600, time=0.1,
            rate=0.02, vol=0.25, option_type="call"
        )

        assert price == 48.5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_options.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/skills/options_skill.py
"""Wrapper for options skill (Greeks, IV, Black-Scholes pricing)."""
from typing import Dict
import sys
sys.path.insert(0, '.')
from skill_wrapper import run_skill, SkillOutputFormat
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError


class OptionsSkill(BaseSkillWrapper):
    """Wrapper for options Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "options"

    def calc_greeks(self, spot: float, strike: float, time: float,
                    rate: float, vol: float, option_type: str) -> Dict[str, float]:
        """Calculate all Greeks for an option."""
        result = run_skill(self.skill_name, "greeks",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --vol {vol} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Failed to calc Greeks")
        return result.parsed_output or {}

    def calc_bs_price(self, spot: float, strike: float, time: float,
                      rate: float, vol: float, option_type: str) -> float:
        """Calculate Black-Scholes theoretical price."""
        result = run_skill(self.skill_name, "pricing",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --vol {vol} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Failed to calc BS price")
        return (result.parsed_output or {}).get("price", 0.0)

    def calc_iv(self, spot: float, strike: float, time: float,
                rate: float, market_price: float, option_type: str) -> float:
        """Calculate implied volatility from market price."""
        result = run_skill(self.skill_name, "iv",
                          args=f"--spot {spot} --strike {strike} --time {time} "
                               f"--rate {rate} --price {market_price} --type {option_type} --json",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Failed to calc IV")
        return (result.parsed_output or {}).get("iv", 0.0)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills_options.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/skills/options_skill.py tests/test_skills_options.py
git commit -m "feat: add OptionsSkill wrapper for Greeks and pricing"
```

---

### Task 11: Create Technical Analysis Skill Wrapper

**Files:**
- Create: `commodity_pipeline/skills/technical_analysis.py`
- Create: `tests/test_skills_ta.py`

**Step 1: Write the failing test**

```python
# tests/test_skills_ta.py
"""Tests for Technical Analysis skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_ta_skill_name():
    """TechnicalAnalysisSkill should have correct skill name."""
    from commodity_pipeline.skills.technical_analysis import TechnicalAnalysisSkill

    skill = TechnicalAnalysisSkill()
    assert skill.skill_name == "technical-analysis"


def test_ta_skill_to_csv():
    """_to_csv should convert OHLCV bars to CSV format."""
    from commodity_pipeline.skills.technical_analysis import TechnicalAnalysisSkill
    from commodity_pipeline.models import OHLCVBar

    bars = [
        OHLCVBar(date=date(2024, 12, 30), open=100, high=110, low=95, close=105, volume=1000),
        OHLCVBar(date=date(2024, 12, 29), open=98, high=102, low=96, close=100, volume=900),
    ]

    skill = TechnicalAnalysisSkill()
    csv = skill._to_csv(bars)

    assert "date,open,high,low,close,volume" in csv
    assert "2024-12-30,100,110,95,105,1000" in csv
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_ta.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/skills/technical_analysis.py
"""Wrapper for technical-analysis skill."""
from typing import List, Tuple
import sys
sys.path.insert(0, '.')
from skill_wrapper import run_skill, SkillOutputFormat
from commodity_pipeline.models import TechnicalSignals, OHLCVBar, TrendDirection
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError


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

        result = run_skill(self.skill_name, "analyze",
                          args=f"--data '{csv_data}' --indicators {indicators_str} --json",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or f"Failed TA for {code}")

        data = result.parsed_output or {}

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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills_ta.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/skills/technical_analysis.py tests/test_skills_ta.py
git commit -m "feat: add TechnicalAnalysisSkill wrapper"
```

---

### Task 12: Create Scraper Skill Wrapper

**Files:**
- Create: `commodity_pipeline/skills/scraper.py`
- Create: `tests/test_skills_scraper.py`

**Step 1: Write the failing test**

```python
# tests/test_skills_scraper.py
"""Tests for Scraper skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_scraper_skill_name():
    """ScraperSkill should have correct skill name."""
    from commodity_pipeline.skills.scraper import ScraperSkill

    skill = ScraperSkill()
    assert skill.skill_name == "scraper"


def test_scraper_get_news_parses_result():
    """get_news should parse JSON into NewsItem objects."""
    from commodity_pipeline.skills.scraper import ScraperSkill
    from commodity_pipeline.models import NewsItem

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.parsed_output = [
        {
            "title": "螺纹钢期货上涨",
            "source": "eastmoney",
            "url": "https://example.com/1",
            "published": "2024-12-30",
            "summary": "市场看涨",
            "sentiment": "positive"
        }
    ]

    with patch('commodity_pipeline.skills.scraper.run_skill', return_value=mock_result):
        skill = ScraperSkill()
        news = skill.get_news("螺纹钢", sources=["eastmoney"])

        assert len(news) == 1
        assert isinstance(news[0], NewsItem)
        assert news[0].title == "螺纹钢期货上涨"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_scraper.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/skills/scraper.py
"""Wrapper for scraper skill."""
from typing import List
from datetime import datetime
import sys
sys.path.insert(0, '.')
from skill_wrapper import run_skill, SkillOutputFormat
from commodity_pipeline.models import NewsItem
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError


class ScraperSkill(BaseSkillWrapper):
    """Wrapper for scraper Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "scraper"

    def get_news(self, keyword: str, sources: List[str] = None,
                 max_per_source: int = 5) -> List[NewsItem]:
        """Scrape news articles for a keyword from specified sources."""
        sources = sources or ["eastmoney", "sina"]
        sources_str = ",".join(sources)

        result = run_skill(self.skill_name, "news",
                          args=f"--keyword '{keyword}' --sources {sources_str} --max {max_per_source} --json",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or f"Failed to get news for {keyword}")

        news_items = []
        for item in result.parsed_output or []:
            published = item.get("published", "")
            if isinstance(published, str):
                try:
                    published = datetime.strptime(published, "%Y-%m-%d").date()
                except ValueError:
                    published = datetime.now().date()

            news_items.append(NewsItem(
                title=item.get("title", ""),
                source=item.get("source", ""),
                url=item.get("url", ""),
                published=published,
                summary=item.get("summary"),
                sentiment=item.get("sentiment")
            ))

        return news_items
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills_scraper.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/skills/scraper.py tests/test_skills_scraper.py
git commit -m "feat: add ScraperSkill wrapper for news"
```

---

### Task 13: Create Gmail Skill Wrapper

**Files:**
- Create: `commodity_pipeline/skills/gmail.py`
- Create: `tests/test_skills_gmail.py`

**Step 1: Write the failing test**

```python
# tests/test_skills_gmail.py
"""Tests for Gmail skill wrapper."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_gmail_skill_name():
    """GmailSkill should have correct skill name."""
    from commodity_pipeline.skills.gmail import GmailSkill

    skill = GmailSkill()
    assert skill.skill_name == "gmail-reader"


def test_gmail_get_alerts():
    """get_alerts should return list of NewsItem objects."""
    from commodity_pipeline.skills.gmail import GmailSkill
    from commodity_pipeline.models import NewsItem

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.parsed_output = [
        {
            "title": "Google Alert - 螺纹钢",
            "source": "gmail",
            "url": "https://mail.google.com/1",
            "published": "2024-12-30",
            "summary": "New article about 螺纹钢"
        }
    ]

    with patch('commodity_pipeline.skills.gmail.run_skill', return_value=mock_result):
        skill = GmailSkill()
        alerts = skill.get_alerts()

        assert len(alerts) == 1
        assert isinstance(alerts[0], NewsItem)
        assert alerts[0].source == "gmail"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_skills_gmail.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/skills/gmail.py
"""Wrapper for gmail-reader skill."""
from typing import List
from datetime import datetime
import sys
sys.path.insert(0, '.')
from skill_wrapper import run_skill, SkillOutputFormat
from commodity_pipeline.models import NewsItem
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError


class GmailSkill(BaseSkillWrapper):
    """Wrapper for gmail-reader Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "gmail-reader"

    def get_alerts(self, query: str = "from:alerts-noreply@google.com") -> List[NewsItem]:
        """Get today's Google Alerts from Gmail."""
        result = run_skill(self.skill_name, "search",
                          args=f"--query '{query}' --today --json",
                          output_format=SkillOutputFormat.JSON)
        if not result.success:
            raise SkillError(self.skill_name, result.error or "Failed to get Gmail alerts")

        alerts = []
        for item in result.parsed_output or []:
            published = item.get("published", "")
            if isinstance(published, str):
                try:
                    published = datetime.strptime(published, "%Y-%m-%d").date()
                except ValueError:
                    published = datetime.now().date()

            alerts.append(NewsItem(
                title=item.get("title", item.get("subject", "")),
                source="gmail",
                url=item.get("url", ""),
                published=published,
                summary=item.get("summary", item.get("snippet", "")),
                sentiment=item.get("sentiment")
            ))

        return alerts
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_skills_gmail.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/skills/gmail.py tests/test_skills_gmail.py
git commit -m "feat: add GmailSkill wrapper for alerts"
```

---

## Phase 3: Pipeline Stages

### Task 14: Create Screening Stage

**Files:**
- Create: `commodity_pipeline/stages/screening.py`
- Create: `tests/test_stages_screening.py`

**Step 1: Write the failing test**

```python
# tests/test_stages_screening.py
"""Tests for Screening stage."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_screening_stage_filter_top_movers():
    """_filter_top_movers should return top N gainers and losers."""
    from commodity_pipeline.stages.screening import ScreeningStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity

    commodities = [
        Commodity("a", "A", "X", "a1", 100, 5.0, 3.0, 2.0),   # +5% 1d
        Commodity("b", "B", "X", "b1", 100, -4.0, -3.0, -2.0), # -4% 1d
        Commodity("c", "C", "X", "c1", 100, 3.0, 2.0, 1.0),   # +3% 1d
        Commodity("d", "D", "X", "d1", 100, -2.0, -1.0, 0.0), # -2% 1d
        Commodity("e", "E", "X", "e1", 100, 1.0, 0.5, 0.0),   # +1% 1d
    ]

    config = PipelineConfig(top_n_movers=2)
    stage = ScreeningStage(config)

    result = stage._filter_top_movers(commodities, period="1d")

    # Should have top 2 gainers + top 2 losers = 4 unique
    assert len(result) <= 4
    codes = [c.code for c in result]
    assert "a" in codes  # top gainer
    assert "b" in codes  # top loser
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_stages_screening.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/stages/screening.py
"""Screening stage - Steps 1-4: Get contracts, calc changes, filter top movers."""
import asyncio
from typing import List, Set
from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import Commodity
from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class ScreeningStage:
    """Screen commodities and filter to top movers."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.futures_skill = ChinaFuturesSkill()

    async def run(self) -> List[Commodity]:
        """Run screening: get contracts, filter to top movers."""
        # Step 1: Get all main contracts
        logger.info("Getting main contracts...")
        all_commodities = self.futures_skill.get_main_contracts()
        logger.info(f"Got {len(all_commodities)} contracts")

        # Steps 2-3: Filter top movers for each period
        selected: Set[str] = set()
        for period in self.config.periods:
            period_key = f"{period}d"
            top_movers = self._filter_top_movers(all_commodities, period_key)
            for c in top_movers:
                selected.add(c.code)
            logger.info(f"Period {period_key}: {len(top_movers)} movers")

        # Step 4: Deduplicate and return
        result = [c for c in all_commodities if c.code in selected]
        logger.info(f"Selected {len(result)} unique commodities")
        return result

    def _filter_top_movers(self, commodities: List[Commodity], period: str) -> List[Commodity]:
        """Filter to top N gainers and top N losers for a period."""
        # Get the change value for the period
        def get_change(c: Commodity) -> float:
            if period == "1d":
                return c.change_1d
            elif period == "3d":
                return c.change_3d
            elif period == "5d":
                return c.change_5d
            return 0.0

        # Sort by change
        sorted_by_change = sorted(commodities, key=get_change, reverse=True)

        # Top N gainers (highest positive change)
        top_gainers = sorted_by_change[:self.config.top_n_movers]

        # Top N losers (lowest/most negative change)
        top_losers = sorted_by_change[-self.config.top_n_movers:]

        # Combine and deduplicate
        result = []
        seen = set()
        for c in top_gainers + top_losers:
            if c.code not in seen:
                result.append(c)
                seen.add(c.code)

        return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_stages_screening.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/stages/screening.py tests/test_stages_screening.py
git commit -m "feat: add ScreeningStage for filtering top movers"
```

---

### Task 15: Create Technical Stage with Parallelization

**Files:**
- Create: `commodity_pipeline/stages/technical.py`
- Create: `tests/test_stages_technical.py`

**Step 1: Write the failing test**

```python
# tests/test_stages_technical.py
"""Tests for Technical stage."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_technical_stage_analyze_one():
    """_analyze_one should get OHLCV and run TA for one commodity."""
    from commodity_pipeline.stages.technical import TechnicalStage
    from commodity_pipeline.config import PipelineConfig
    from commodity_pipeline.models import Commodity, OHLCVBar, TechnicalSignals, TrendDirection

    config = PipelineConfig()
    stage = TechnicalStage(config)

    commodity = Commodity("rb2501", "螺纹钢", "SHFE", "rb2501", 3500, 1.0, 2.0, -0.5)

    # Mock the skill calls
    mock_ohlcv = [
        OHLCVBar(date(2024, 12, 30), 3500, 3550, 3480, 3520, 100000)
    ]
    mock_signals = TechnicalSignals(
        "rb2501", "buy", "buy", 65.0, "neutral", "middle",
        "buy", 50.0, "up", "neutral", TrendDirection.BULLISH, 7
    )

    with patch.object(stage.futures_skill, 'get_ohlcv', return_value=mock_ohlcv):
        with patch.object(stage.ta_skill, 'analyze', return_value=mock_signals):
            result = stage._analyze_one(commodity)

            assert result.commodity_code == "rb2501"
            assert result.overall_trend == TrendDirection.BULLISH
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_stages_technical.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# commodity_pipeline/stages/technical.py
"""Technical stage - Steps 5-6: Get OHLCV, run technical analysis."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import Commodity, TechnicalSignals
from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
from commodity_pipeline.skills.technical_analysis import TechnicalAnalysisSkill
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class TechnicalStage:
    """Get OHLCV data and run technical analysis for commodities."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.futures_skill = ChinaFuturesSkill()
        self.ta_skill = TechnicalAnalysisSkill()

    async def run(self, commodities: List[Commodity]) -> Dict[str, TechnicalSignals]:
        """Run technical analysis for all commodities in parallel."""
        logger.info(f"Starting technical analysis for {len(commodities)} commodities")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, self._analyze_one, commodity)
                for commodity in commodities
            ]
            results = await asyncio.gather(*tasks)

        return {r.commodity_code: r for r in results}

    def _analyze_one(self, commodity: Commodity) -> TechnicalSignals:
        """Analyze a single commodity (runs in thread)."""
        logger.info(f"Analyzing {commodity.code}")

        # Step 5: Get OHLCV
        ohlcv = self.futures_skill.get_ohlcv(
            contract=commodity.main_contract,
            days=self.config.ohlcv_days
        )
        logger.debug(f"Got {len(ohlcv)} bars for {commodity.code}")

        # Step 6: Technical analysis
        signals = self.ta_skill.analyze(
            commodity.code, ohlcv, self.config.indicators
        )
        logger.info(f"Completed TA for {commodity.code}: {signals.overall_trend.value}")

        return signals
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_stages_technical.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add commodity_pipeline/stages/technical.py tests/test_stages_technical.py
git commit -m "feat: add TechnicalStage with ThreadPool parallelization"
```

---

## Remaining Tasks (16-25)

Due to length, I'll summarize the remaining tasks. Each follows the same TDD pattern:

### Task 16: Create Options Stage
- File: `commodity_pipeline/stages/options.py`
- Gets options chain, filters top by volume, calculates Greeks/IV/BS for each

### Task 17: Create News Stage
- File: `commodity_pipeline/stages/news.py`
- Scrapes news from configured sources for each commodity

### Task 18: Create Alerts Stage
- File: `commodity_pipeline/stages/alerts.py`
- Gets Gmail alerts

### Task 19: Create Strategy Stage
- File: `commodity_pipeline/stages/strategy.py`
- Synthesizes all data, generates 3+ strategy recommendations per commodity

### Task 20: Create Terminal Output
- File: `commodity_pipeline/output/terminal.py`
- Rich formatted terminal output with colors

### Task 21: Create Markdown Output
- File: `commodity_pipeline/output/markdown.py`
- Generates `reports/YYYY-MM-DD-commodity-analysis.md`

### Task 22: Create JSON Output
- File: `commodity_pipeline/output/json_export.py`
- Exports full results to JSON

### Task 23: Create Main Entry Point
- File: `commodity_pipeline/run.py`
- CLI with argparse, orchestrates all stages

### Task 24: Integration Test
- File: `tests/test_integration.py`
- End-to-end test with mocked skills

### Task 25: Update pyproject.toml and README
- Add pytest dependency
- Document usage

---

**Implementation order:** Tasks 1-15 first (foundation + skill wrappers + first stages), then 16-25.

**Total estimated tasks:** 25 tasks, ~2-5 min each = ~1-2 hours of focused work.
