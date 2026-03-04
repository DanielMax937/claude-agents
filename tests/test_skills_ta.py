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


def test_ta_skill_extract_json_from_mixed_output():
    """_extract_json should extract JSON from mixed output with progress messages."""
    from commodity_pipeline.skills.technical_analysis import TechnicalAnalysisSkill

    skill = TechnicalAnalysisSkill()

    # Simulate output from analyze.py with progress messages before JSON
    mixed_output = """Loading data from /tmp/xyz.csv...
Loaded 15 bars
Calculating technical indicators...
Analyzing patterns...
Generating trading signals...

============================================================
JSON OUTPUT
============================================================
{"symbol": "CU", "signals": {"signal": "BUY", "strength": 45}, "patterns": {}}"""

    result = skill._extract_json(mixed_output)

    assert result["symbol"] == "CU"
    assert result["signals"]["signal"] == "BUY"
    assert result["signals"]["strength"] == 45


def test_ta_skill_extract_json_empty_output():
    """_extract_json should return empty dict for empty output."""
    from commodity_pipeline.skills.technical_analysis import TechnicalAnalysisSkill

    skill = TechnicalAnalysisSkill()
    assert skill._extract_json("") == {}
    assert skill._extract_json(None) == {}
