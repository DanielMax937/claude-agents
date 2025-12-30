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
