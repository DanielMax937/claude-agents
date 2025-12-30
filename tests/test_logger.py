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
