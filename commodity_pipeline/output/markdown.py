"""Markdown output formatter for reports."""
from datetime import datetime
from typing import List, Dict, Optional

from commodity_pipeline.models import (
    Commodity, TechnicalSignals, TrendDirection,
    OptionContract, NewsItem, StrategyRecommendation
)


class MarkdownOutput:
    """Format pipeline results as Markdown documents."""

    def format_commodity(
        self,
        commodity: Commodity,
        technical: Optional[TechnicalSignals],
        options: List[OptionContract],
        news: List[NewsItem],
        strategies: List[StrategyRecommendation]
    ) -> str:
        """Format a single commodity section."""
        lines = []

        # Header
        trend_emoji = "📈" if technical and technical.overall_trend == TrendDirection.BULLISH else \
                     "📉" if technical and technical.overall_trend == TrendDirection.BEARISH else "➡️"
        lines.append(f"## {commodity.code} - {commodity.name} {trend_emoji}")
        lines.append("")

        # Basic info table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Exchange | {commodity.exchange} |")
        lines.append(f"| Price | {commodity.price:.2f} |")
        lines.append(f"| 1D Change | {commodity.change_1d:+.2f}% |")
        lines.append(f"| 3D Change | {commodity.change_3d:+.2f}% |")
        lines.append(f"| 5D Change | {commodity.change_5d:+.2f}% |")
        lines.append("")

        # Technical Analysis
        if technical:
            lines.append("### Technical Analysis")
            lines.append("")
            lines.append(f"**Overall Trend:** {technical.overall_trend.value.upper()} (Strength: {technical.strength}/10)")
            lines.append("")
            lines.append("| Indicator | Signal | Value |")
            lines.append("|-----------|--------|-------|")
            lines.append(f"| MA | {technical.ma_signal} | - |")
            lines.append(f"| MACD | {technical.macd_signal} | - |")
            lines.append(f"| RSI | {technical.rsi_signal} | {technical.rsi_value:.1f} |")
            lines.append(f"| Bollinger | {technical.boll_position} | - |")
            lines.append(f"| KDJ | {technical.kdj_signal} | - |")
            lines.append(f"| ATR | - | {technical.atr_value:.2f} |")
            lines.append(f"| OBV | {technical.obv_trend} | - |")
            lines.append(f"| CCI | {technical.cci_signal} | - |")
            lines.append("")

        # Options
        if options:
            lines.append("### Options")
            lines.append("")
            lines.append("| Code | Type | Strike | IV | Delta | Mispricing |")
            lines.append("|------|------|--------|-----|-------|------------|")
            for opt in options[:5]:
                lines.append(f"| {opt.code} | {opt.option_type} | {opt.strike:.0f} | "
                           f"{opt.iv:.1%} | {opt.delta:.2f} | {opt.mispricing:+.2f} |")
            lines.append("")

        # News
        if news:
            lines.append("### News")
            lines.append("")
            for n in news[:5]:
                sentiment = f" ({n.sentiment})" if n.sentiment else ""
                lines.append(f"- [{n.title}]({n.url}){sentiment} - {n.source}")
            lines.append("")

        # Strategies
        if strategies:
            lines.append("### Recommended Strategies")
            lines.append("")
            for s in strategies[:3]:
                conf_pct = s.confidence * 10
                lines.append(f"#### {s.name}")
                lines.append(f"- **Type:** {s.type}")
                lines.append(f"- **Confidence:** {conf_pct}%")
                lines.append(f"- **Max Profit:** {'∞' if s.max_profit == float('inf') else f'{s.max_profit:.2f}'}")
                lines.append(f"- **Max Loss:** {s.max_loss:.2f}")
                lines.append(f"- **Rationale:** {s.rationale}")
                lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def format_all(
        self,
        commodities: List[Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]],
        strategies: Dict[str, List[StrategyRecommendation]],
        alerts: List[NewsItem]
    ) -> str:
        """Format complete markdown report."""
        lines = []

        # Document header
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines.append("# Commodity Analysis Report")
        lines.append("")
        lines.append(f"*Generated: {now}*")
        lines.append("")

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for c in commodities:
            lines.append(f"- [{c.code} - {c.name}](#{c.code.lower()}-{c.name})")
        lines.append("")

        # Alerts section
        if alerts:
            lines.append("## ⚠️ Alerts")
            lines.append("")
            for alert in alerts[:10]:
                lines.append(f"- **{alert.title}** - {alert.source}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Commodity | Price | 1D% | Trend | Strength |")
        lines.append("|-----------|-------|-----|-------|----------|")
        for c in commodities:
            tech = technical.get(c.code)
            trend = tech.overall_trend.value if tech else "-"
            strength = f"{tech.strength}/10" if tech else "-"
            lines.append(f"| {c.code} ({c.name}) | {c.price:.2f} | {c.change_1d:+.2f}% | {trend} | {strength} |")
        lines.append("")

        # Detailed sections
        for commodity in commodities:
            code = commodity.code
            lines.append(self.format_commodity(
                commodity,
                technical.get(code),
                options.get(code, []),
                news.get(code, []),
                strategies.get(code, [])
            ))

        return "\n".join(lines)

    def save(
        self,
        filepath: str,
        commodities: List[Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]],
        strategies: Dict[str, List[StrategyRecommendation]],
        alerts: List[NewsItem]
    ) -> None:
        """Save markdown report to file."""
        content = self.format_all(commodities, technical, options, news, strategies, alerts)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
