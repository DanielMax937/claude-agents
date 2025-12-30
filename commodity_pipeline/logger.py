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
