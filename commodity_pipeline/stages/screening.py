"""Screening stage - Steps 1-4: Get contracts, calc changes, filter top movers."""
import asyncio
from typing import List, Set

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import Commodity
from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class ScreeningStage:
    """Screen commodities and filter to top movers."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.futures_skill = ChinaFuturesSkill()

    async def run(self) -> List[Commodity]:
        """Run screening: get contracts, filter to top movers."""
        # Step 1: Get all main contracts
        logger.info("Getting main contracts...")
        all_commodities = self.futures_skill.get_main_contracts()
        logger.info(f"Got {len(all_commodities)} contracts")

        # Steps 2-3: Filter top movers for each period
        selected: Set[str] = set()
        for period in self.config.periods:
            period_key = f"{period}d"
            top_movers = self._filter_top_movers(all_commodities, period_key)
            for c in top_movers:
                selected.add(c.code)
            logger.info(f"Period {period_key}: {len(top_movers)} movers")

        # Step 4: Deduplicate and return
        result = [c for c in all_commodities if c.code in selected]
        logger.info(f"Selected {len(result)} unique commodities")
        return result

    def _filter_top_movers(self, commodities: List[Commodity], period: str) -> List[Commodity]:
        """Filter to top N gainers and top N losers for a period."""
        # Get the change value for the period
        def get_change(c: Commodity) -> float:
            if period == "1d":
                return c.change_1d
            elif period == "3d":
                return c.change_3d
            elif period == "5d":
                return c.change_5d
            return 0.0

        # Sort by change
        sorted_by_change = sorted(commodities, key=get_change, reverse=True)

        # Top N gainers (highest positive change)
        top_gainers = sorted_by_change[:self.config.top_n_movers]

        # Top N losers (lowest/most negative change)
        top_losers = sorted_by_change[-self.config.top_n_movers:]

        # Combine and deduplicate
        result = []
        seen = set()
        for c in top_gainers + top_losers:
            if c.code not in seen:
                result.append(c)
                seen.add(c.code)

        return result
