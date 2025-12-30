"""Wrapper for gmail-reader skill."""
from typing import List
from datetime import datetime

from commodity_pipeline.models import NewsItem
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class GmailSkill(BaseSkillWrapper):
    """Wrapper for gmail-reader Claude Code skill."""

    @property
    def skill_name(self) -> str:
        return "gmail-reader"

    def get_alerts(self, query: str = "from:alerts-noreply@google.com") -> List[NewsItem]:
        """Get today's Google Alerts from Gmail."""
        result = self._run("search",
                          args=f"--query '{query}' --today --json",
                          output_format=SkillOutputFormat.JSON)

        alerts = []
        for item in result.output or []:
            published = item.get("published", "")
            if isinstance(published, str):
                try:
                    published = datetime.strptime(published, "%Y-%m-%d").date()
                except ValueError:
                    published = datetime.now().date()

            alerts.append(NewsItem(
                title=item.get("title", item.get("subject", "")),
                source="gmail",
                url=item.get("url", ""),
                published=published,
                summary=item.get("summary", item.get("snippet", "")),
                sentiment=item.get("sentiment")
            ))

        return alerts
