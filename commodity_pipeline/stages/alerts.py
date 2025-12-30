"""Alerts stage - Step 9: Get Gmail alerts for market news."""
import asyncio
from typing import List

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import Commodity, NewsItem
from commodity_pipeline.skills.gmail import GmailSkill
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class AlertsStage:
    """Get Gmail alerts for market news."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.gmail_skill = GmailSkill()

    async def run(self) -> List[NewsItem]:
        """Get all Gmail alerts."""
        logger.info("Fetching Gmail alerts")
        alerts = self.gmail_skill.get_alerts()
        logger.info(f"Got {len(alerts)} alerts from Gmail")
        return alerts

    async def run_filtered(self, commodities: List[Commodity]) -> List[NewsItem]:
        """Get Gmail alerts filtered by commodity names."""
        logger.info(f"Fetching Gmail alerts for {len(commodities)} commodities")

        all_alerts = await self.run()

        # Build keyword list from commodity names
        keywords = [c.name for c in commodities]

        # Filter alerts that mention any commodity
        filtered = []
        for alert in all_alerts:
            for keyword in keywords:
                if keyword in alert.title or (alert.summary and keyword in alert.summary):
                    filtered.append(alert)
                    break

        logger.info(f"Filtered to {len(filtered)} relevant alerts")
        return filtered
