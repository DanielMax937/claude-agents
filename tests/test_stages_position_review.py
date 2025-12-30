"""Tests for PositionReviewStage."""
import pytest
from datetime import date, timedelta
from commodity_pipeline.stages.position_review import PositionReviewStage
from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import (
    Commodity, TechnicalSignals, TrendDirection,
    OptionContract, NewsItem
)


def test_position_review_stage_initialization():
    """Should initialize with config."""
    config = PipelineConfig(signal_weights={"greeks": 40, "technical": 30, "time": 20, "news": 10})
    stage = PositionReviewStage(config)

    assert stage.config.signal_weights["greeks"] == 40


@pytest.fixture
def mock_holding():
    """A sample holding for testing."""
    return {
        "code": "CU2501-C-75000",
        "symbol": "CU",
        "expiry": "2025-01-15",
        "strike": 75000,
        "type": "call",
        "quantity": 2,
        "avg_cost": 1200
    }


@pytest.fixture
def mock_commodity():
    """A sample commodity."""
    return Commodity("CU", "铜", "SHFE", "cu2501", 74520, 1.5, 2.0, -0.5)


@pytest.fixture
def mock_technical():
    """Mock technical signals - bullish."""
    return TechnicalSignals(
        commodity_code="CU",
        ma_signal="buy",
        macd_signal="buy",
        rsi_value=58.0,
        rsi_signal="neutral",
        boll_position="middle",
        kdj_signal="buy",
        atr_value=150.0,
        obv_trend="up",
        cci_signal="buy",
        overall_trend=TrendDirection.BULLISH,
        strength=7
    )


@pytest.fixture
def mock_option_contract():
    """Mock option contract with Greeks."""
    # Always set expiry 16 days from now (in theta decay zone)
    expiry = date.today() + timedelta(days=16)

    return OptionContract(
        code="CU2501-C-75000",
        underlying="CU",
        strike=75000,
        expiry=expiry,
        option_type="call",
        market_price=1450,
        volume=1000,
        iv=0.185,
        delta=0.52,
        gamma=0.00008,
        theta=-12.3,
        vega=42.1,
        rho=0.15,
        bs_value=1430,
        mispricing=20
    )


def test_score_greeks_bullish_aligned(mock_holding, mock_option_contract):
    """Should score based on Greeks factors."""
    config = PipelineConfig()
    stage = PositionReviewStage(config)

    score = stage._score_greeks(
        position_data=mock_holding,
        greeks=mock_option_contract,
        spot=74520,
        trend="bullish"
    )

    # Score combines delta (+20), gamma risk (-15 for 0.00008), theta decay zone (-10 for ~16 DTE)
    # 50 + 20 - 15 - 10 = 45 (approximately)
    assert 40 <= score <= 50


def test_score_greeks_bearish_mismatch(mock_holding, mock_option_contract):
    """Should score lower when call position conflicts with bearish trend."""
    config = PipelineConfig()
    stage = PositionReviewStage(config)

    score = stage._score_greeks(
        position_data=mock_holding,
        greeks=mock_option_contract,
        spot=74520,
        trend="bearish"
    )

    # Should be below baseline - call in bearish trend
    assert score < 50


def test_score_technical_bullish(mock_commodity, mock_technical):
    """Should score high for strong bullish technicals."""
    config = PipelineConfig()
    stage = PositionReviewStage(config)

    score = stage._score_technical(mock_commodity, mock_technical)

    # Strong bullish (strength 7) should score high
    assert score >= 70


def test_score_time_optimal_dte(mock_holding, mock_option_contract):
    """Should score well for optimal DTE (30-60 days)."""
    config = PipelineConfig()
    stage = PositionReviewStage(config)

    # Create a contract with 45 DTE (optimal zone)
    expiry_45 = date.today() + timedelta(days=45)
    contract_45 = OptionContract(
        code="CU2501-C-75000",
        underlying="CU",
        strike=75000,
        expiry=expiry_45,
        option_type="call",
        market_price=1450,
        volume=1000,
        iv=0.185,
        delta=0.52,
        gamma=0.00008,
        theta=-12.3,
        vega=42.1,
        rho=0.15,
        bs_value=1430,
        mispricing=20
    )

    score = stage._score_time(mock_holding, contract_45)

    # 45 DTE is optimal - should score well
    assert score >= 60


def test_score_news_bullish():
    """Should score based on news sentiment."""
    config = PipelineConfig()
    stage = PositionReviewStage(config)

    news = [
        NewsItem("Positive copper demand", "eastmoney", "url1", date.today(), summary="Good demand", sentiment="positive"),
        NewsItem("Copper supply constrained", "sina", "url2", date.today(), summary="Low supply", sentiment="positive"),
        NewsItem("Copper neutral", "eastmoney", "url3", date.today(), summary="Neutral", sentiment="neutral"),
    ]

    score = stage._score_news(news)

    # 2 positive, 1 neutral - should score well
    assert score >= 70


def test_generate_recommendation():
    """Should generate HOLD/ADJUST/CLOSE based on overall score."""
    config = PipelineConfig()
    stage = PositionReviewStage(config)

    # High score -> HOLD
    rec = stage._generate_recommendation(80, "bullish")
    assert rec == "HOLD"

    # Medium score -> ADJUST
    rec = stage._generate_recommendation(55, "neutral")
    assert rec == "ADJUST"

    # Low score -> CLOSE
    rec = stage._generate_recommendation(30, "bearish")
    assert rec == "CLOSE"
