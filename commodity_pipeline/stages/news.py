"""News stage - Step 8: Scrape news from Chinese finance sites."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import Commodity, NewsItem
from commodity_pipeline.skills.scraper import ScraperSkill
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class NewsStage:
    """Scrape news articles for commodities from Chinese finance sites."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.scraper_skill = ScraperSkill()

    async def run(self, commodities: List[Commodity]) -> Dict[str, List[NewsItem]]:
        """Scrape news for all commodities in parallel."""
        logger.info(f"Starting news scraping for {len(commodities)} commodities")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, self._get_news_for_commodity, commodity)
                for commodity in commodities
            ]
            results = await asyncio.gather(*tasks)

        return {
            commodities[i].code: results[i]
            for i in range(len(commodities))
        }

    def _get_news_for_commodity(self, commodity: Commodity) -> List[NewsItem]:
        """Get news for a single commodity (runs in thread)."""
        logger.info(f"Scraping news for {commodity.name}")

        news = self.scraper_skill.get_news(
            commodity.name,
            sources=list(self.config.news_sources),
            max_per_source=self.config.max_news_per_source
        )

        logger.info(f"Got {len(news)} articles for {commodity.name}")
        return news
