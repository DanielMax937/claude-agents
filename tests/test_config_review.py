"""Tests for review mode configuration."""
import pytest
from commodity_pipeline.config import PipelineConfig


def test_default_config_is_discovery_mode():
    """Default config should be discovery mode."""
    config = PipelineConfig()

    assert config.mode == "discovery"
    assert config.holdings is None


def test_review_mode_config():
    """Should accept holdings for review mode."""
    holdings = [{"code": "CU2501-C-75000", "quantity": 2}]

    config = PipelineConfig(
        mode="review",
        holdings=holdings
    )

    assert config.mode == "review"
    assert config.holdings == holdings


def test_signal_weights_default():
    """Default signal weights should be balanced."""
    config = PipelineConfig()

    assert config.signal_weights == {
        "greeks": 30,
        "technical": 30,
        "time": 20,
        "news": 20
    }


def test_signal_weights_custom():
    """Should accept custom signal weights."""
    config = PipelineConfig(
        signal_weights={"greeks": 40, "technical": 40, "time": 10, "news": 10}
    )

    assert config.signal_weights["greeks"] == 40
    assert config.signal_weights["time"] == 10
