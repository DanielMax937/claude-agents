"""Terminal output formatter with ANSI colors."""
from typing import List, Dict, Optional, Any

from commodity_pipeline.models import (
    Commodity, TechnicalSignals, TrendDirection,
    OptionContract, NewsItem, StrategyRecommendation
)


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


class TerminalOutput:
    """Format pipeline results for terminal display."""

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors

    def _c(self, color: str, text: str) -> str:
        """Apply color if colors are enabled."""
        if not self.use_colors:
            return text
        return f"{color}{text}{Colors.RESET}"

    def _trend_color(self, is_bullish: bool) -> str:
        """Get color code for trend direction."""
        return Colors.GREEN if is_bullish else Colors.RED

    def _recommendation_color(self, recommendation: str) -> str:
        """Get color code for recommendation."""
        if recommendation == "HOLD":
            return Colors.GREEN
        elif recommendation == "ADJUST":
            return Colors.YELLOW
        elif recommendation == "CLOSE":
            return Colors.RED
        return Colors.RESET

    def format_commodity_summary(
        self,
        commodity: Commodity,
        technical: Optional[TechnicalSignals],
        options: List[OptionContract],
        news: List[NewsItem],
        strategies: List[StrategyRecommendation]
    ) -> str:
        """Format summary for a single commodity."""
        lines = []

        # Header
        trend_str = technical.overall_trend.value if technical else "unknown"
        is_bullish = technical and technical.overall_trend == TrendDirection.BULLISH
        trend_colored = self._c(self._trend_color(is_bullish), trend_str.upper())

        lines.append(self._c(Colors.BOLD, f"═══ {commodity.code} ({commodity.name}) ═══"))
        lines.append(f"Exchange: {commodity.exchange}  |  Price: {commodity.price:.2f}")
        lines.append(f"Changes: 1d={commodity.change_1d:+.2f}% | 3d={commodity.change_3d:+.2f}% | 5d={commodity.change_5d:+.2f}%")
        lines.append(f"Trend: {trend_colored}")

        # Technical signals
        if technical:
            lines.append("")
            lines.append(self._c(Colors.CYAN, "── Technical Signals ──"))
            lines.append(f"  MA: {technical.ma_signal}  |  MACD: {technical.macd_signal}")
            lines.append(f"  RSI: {technical.rsi_value:.1f} ({technical.rsi_signal})")
            lines.append(f"  BOLL: {technical.boll_position}  |  KDJ: {technical.kdj_signal}")
            lines.append(f"  Strength: {technical.strength}/10")

        # Options
        if options:
            lines.append("")
            lines.append(self._c(Colors.YELLOW, "── Options ──"))
            for opt in options[:3]:
                lines.append(f"  {opt.code}: Strike={opt.strike} | IV={opt.iv:.2%} | Δ={opt.delta:.2f}")

        # News
        if news:
            lines.append("")
            lines.append(self._c(Colors.MAGENTA, "── News ──"))
            for n in news[:3]:
                sentiment_icon = "📈" if n.sentiment == "positive" else "📉" if n.sentiment == "negative" else "📊"
                lines.append(f"  {sentiment_icon} {n.title[:50]}")

        # Strategies
        if strategies:
            lines.append("")
            lines.append(self._c(Colors.BLUE, "── Strategies ──"))
            for s in strategies[:3]:
                conf_bar = "█" * s.confidence + "░" * (10 - s.confidence)
                lines.append(f"  {s.name} [{conf_bar}] {s.type}")
                lines.append(f"    {s.rationale[:60]}...")

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
        """Format complete pipeline report."""
        lines = []

        # Header
        lines.append(self._c(Colors.BOLD, "╔════════════════════════════════════════════════╗"))
        lines.append(self._c(Colors.BOLD, "║     COMMODITY ANALYSIS PIPELINE REPORT         ║"))
        lines.append(self._c(Colors.BOLD, "╚════════════════════════════════════════════════╝"))
        lines.append("")

        # Alerts section
        if alerts:
            lines.append(self._c(Colors.RED, "⚠️  ALERTS ⚠️"))
            for alert in alerts[:5]:
                lines.append(f"  • {alert.title}")
            lines.append("")

        # Each commodity
        for commodity in commodities:
            code = commodity.code
            lines.append(self.format_commodity_summary(
                commodity,
                technical.get(code),
                options.get(code, []),
                news.get(code, []),
                strategies.get(code, [])
            ))

        # Footer
        lines.append(self._c(Colors.BOLD, "═" * 50))
        lines.append(f"Total commodities analyzed: {len(commodities)}")

        return "\n".join(lines)

    def print_report(self, report: str) -> None:
        """Print the report to terminal."""
        print(report)

    def format_position_review(self, positions: List[Dict[str, Any]]) -> str:
        """Format position review results for terminal display."""
        lines = []

        # Header
        lines.append(self._c(Colors.BOLD, "╔════════════════════════════════════════════════╗"))
        lines.append(self._c(Colors.BOLD, "║         POSITION REVIEW REPORT                  ║"))
        lines.append(self._c(Colors.BOLD, "╚════════════════════════════════════════════════╝"))
        lines.append("")

        for pos in positions:
            code = pos.get("position_code", "UNKNOWN")
            signal = pos.get("signal", "neutral")
            confidence = pos.get("confidence", 0.0)
            scores = pos.get("scores", {})
            metrics = pos.get("metrics", {})
            recommendation = pos.get("recommendation", "UNKNOWN")
            reason = pos.get("reason", "")

            # Position header
            lines.append(self._c(Colors.BOLD, f"═══ {code} ═══"))

            # Signal and confidence
            is_bullish = signal == "bullish"
            signal_colored = self._c(self._trend_color(is_bullish), signal.upper())
            lines.append(f"Signal: {signal_colored}  |  Confidence: {int(confidence * 100)}%")

            # Recommendation
            rec_colored = self._c(self._recommendation_color(recommendation), recommendation)
            lines.append(f"Recommendation: {rec_colored}")

            # Scores breakdown
            lines.append("")
            lines.append(self._c(Colors.CYAN, "── Scores ──"))
            for category, score in scores.items():
                category_display = category.capitalize()
                bar = self._score_bar(score)
                lines.append(f"  {category_display}: {score}/100 [{bar}]")

            # Metrics
            if metrics:
                lines.append("")
                lines.append(self._c(Colors.YELLOW, "── Metrics ──"))
                lines.append(f"  Spot: {metrics.get('spot', 'N/A')}")
                lines.append(f"  Strike: {metrics.get('strike', 'N/A')}")
                lines.append(f"  DTE: {metrics.get('dte', 'N/A')} days")
                lines.append(f"  ITM Amount: {metrics.get('itm_amount', 'N/A')}")
                lines.append("")
                lines.append(self._c(Colors.CYAN, "  Greeks:"))
                lines.append(f"    Delta: {metrics.get('delta', 'N/A')}")
                lines.append(f"    Gamma: {metrics.get('gamma', 'N/A')}")
                lines.append(f"    Theta: {metrics.get('theta', 'N/A')}")
                lines.append(f"    Vega: {metrics.get('vega', 'N/A')}")
                lines.append(f"    IV: {metrics.get('iv', 'N/A')}%")

                if "rsi" in metrics:
                    lines.append("")
                    lines.append(self._c(Colors.CYAN, "  Technical:"))
                    lines.append(f"    RSI: {metrics.get('rsi', 'N/A')}")
                    lines.append(f"    Trend: {metrics.get('trend', 'N/A')}")

            # Reason
            if reason:
                lines.append("")
                lines.append(self._c(Colors.MAGENTA, "── Analysis ──"))
                lines.append(f"  {reason}")

            lines.append("")

        # Footer
        lines.append(self._c(Colors.BOLD, "═" * 50))
        lines.append(f"Total positions reviewed: {len(positions)}")

        return "\n".join(lines)

    def _score_bar(self, score: int) -> str:
        """Generate a visual score bar."""
        filled = "█" * (score // 10)
        empty = "░" * (10 - score // 10)
        return f"{filled}{empty}"
