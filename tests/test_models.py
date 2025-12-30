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