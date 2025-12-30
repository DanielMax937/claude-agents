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
