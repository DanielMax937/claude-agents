"""Main pipeline orchestrator for commodity analysis."""
import asyncio
import os
from datetime import datetime
from typing import Dict, Any

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.logger import get_logger, PipelineLogger

# Stages
from commodity_pipeline.stages.screening import ScreeningStage
from commodity_pipeline.stages.technical import TechnicalStage
from commodity_pipeline.stages.options import OptionsStage
from commodity_pipeline.stages.news import NewsStage
from commodity_pipeline.stages.alerts import AlertsStage
from commodity_pipeline.stages.strategy import StrategyStage

# Outputs
from commodity_pipeline.output.terminal import TerminalOutput
from commodity_pipeline.output.markdown import MarkdownOutput
from commodity_pipeline.output.json_output import JSONOutput

logger = get_logger(__name__)


class Pipeline:
    """Main pipeline that orchestrates all stages."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.pipeline_logger = PipelineLogger(self.config.output_dir)

        # Initialize stages
        self.screening_stage = ScreeningStage(self.config)
        self.technical_stage = TechnicalStage(self.config)
        self.options_stage = OptionsStage(self.config)
        self.news_stage = NewsStage(self.config)
        self.alerts_stage = AlertsStage(self.config)
        self.strategy_stage = StrategyStage(self.config)

        # Initialize outputs
        self.terminal_output = TerminalOutput(use_colors=True)
        self.markdown_output = MarkdownOutput()
        self.json_output = JSONOutput()

    async def run(self) -> Dict[str, Any]:
        """Run the complete pipeline."""
        logger.info("Starting commodity analysis pipeline")
        self.pipeline_logger.step_start(0, "Pipeline", "Starting commodity analysis pipeline")

        # Step 1-4: Screening
        self.pipeline_logger.step_start(1, "Screening", "Screening commodities")
        commodities = await self.screening_stage.run()
        self.pipeline_logger.step_complete(1, "Screening", f"Found {len(commodities)} commodities")

        if not commodities:
            logger.warning("No commodities found, pipeline ending early")
            return {
                "commodities": [],
                "technical": {},
                "options": {},
                "news": {},
                "alerts": [],
                "strategies": {}
            }

        # Steps 5-6: Technical Analysis (parallel)
        self.pipeline_logger.step_start(2, "Technical", f"Running TA for {len(commodities)} commodities")
        technical = await self.technical_stage.run(commodities)
        self.pipeline_logger.step_complete(2, "Technical", "Technical analysis complete")

        # Step 7: Options Analysis (parallel)
        self.pipeline_logger.step_start(3, "Options", "Getting options data")
        options = await self.options_stage.run(commodities)
        self.pipeline_logger.step_complete(3, "Options", "Options analysis complete")

        # Step 8: News Scraping (parallel)
        self.pipeline_logger.step_start(4, "News", "Scraping news")
        news = await self.news_stage.run(commodities)
        self.pipeline_logger.step_complete(4, "News", "News scraping complete")

        # Step 9: Gmail Alerts
        self.pipeline_logger.step_start(5, "Alerts", "Getting Gmail alerts")
        alerts = await self.alerts_stage.run_filtered(commodities)
        self.pipeline_logger.step_complete(5, "Alerts", f"Got {len(alerts)} alerts")

        # Step 10: Strategy Generation
        self.pipeline_logger.step_start(6, "Strategy", "Generating strategies")
        strategies = await self.strategy_stage.run(commodities, technical, options, news)
        self.pipeline_logger.step_complete(6, "Strategy", "Strategy generation complete")

        self.pipeline_logger.step_complete(0, "Pipeline", "Pipeline complete")

        return {
            "commodities": commodities,
            "technical": technical,
            "options": options,
            "news": news,
            "alerts": alerts,
            "strategies": strategies
        }

    def output_terminal(self, result: Dict[str, Any]) -> None:
        """Output results to terminal."""
        report = self.terminal_output.format_all(
            result["commodities"],
            result["technical"],
            result["options"],
            result["news"],
            result["strategies"],
            result["alerts"]
        )
        self.terminal_output.print_report(report)

    def save_reports(self, result: Dict[str, Any]) -> None:
        """Save reports to files."""
        # Ensure output directory exists
        os.makedirs(self.config.output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save Markdown
        md_path = os.path.join(self.config.output_dir, f"report_{timestamp}.md")
        self.markdown_output.save(
            md_path,
            result["commodities"],
            result["technical"],
            result["options"],
            result["news"],
            result["strategies"],
            result["alerts"]
        )
        logger.info(f"Saved markdown report to {md_path}")

        # Save JSON
        json_path = os.path.join(self.config.output_dir, f"report_{timestamp}.json")
        self.json_output.save(
            json_path,
            result["commodities"],
            result["technical"],
            result["options"],
            result["news"],
            result["strategies"],
            result["alerts"]
        )
        logger.info(f"Saved JSON report to {json_path}")


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Commodity Analysis Pipeline")
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument("--top-n", type=int, default=3, help="Top N movers to analyze")
    parser.add_argument("--output-dir", type=str, default="reports", help="Output directory")
    parser.add_argument("--no-terminal", action="store_true", help="Skip terminal output")
    parser.add_argument("--no-files", action="store_true", help="Skip file output")

    args = parser.parse_args()

    config = PipelineConfig(
        max_workers=args.workers,
        top_n_movers=args.top_n,
        output_dir=args.output_dir
    )

    pipeline = Pipeline(config)

    try:
        result = await pipeline.run()

        if not args.no_terminal:
            pipeline.output_terminal(result)

        if not args.no_files:
            pipeline.save_reports(result)

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
