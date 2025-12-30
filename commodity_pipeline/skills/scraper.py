"""Wrapper for scraper skill."""
from typing import List
from datetime import datetime

from commodity_pipeline.models import NewsItem
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class ScraperSkill(BaseSkillWrapper):
    """Wrapper for scraper Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "scraper"

    def get_news(self, keyword: str, sources: List[str] = None,
                 max_per_source: int = 5) -> List[NewsItem]:
        """Scrape news articles for a keyword from specified sources."""
        sources = sources or ["eastmoney", "sina"]
        sources_str = ",".join(sources)

        result = self._run("news",
                          args=f"--keyword '{keyword}' --sources {sources_str} --max {max_per_source} --json",
                          output_format=SkillOutputFormat.JSON)

        news_items = []
        for item in result.output or []:
            published = item.get("published", "")
            if isinstance(published, str):
                try:
                    published = datetime.strptime(published, "%Y-%m-%d").date()
                except ValueError:
                    published = datetime.now().date()

            news_items.append(NewsItem(
                title=item.get("title", ""),
                source=item.get("source", ""),
                url=item.get("url", ""),
                published=published,
                summary=item.get("summary"),
                sentiment=item.get("sentiment")
            ))

        return news_items
