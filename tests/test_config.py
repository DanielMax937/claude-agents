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
