"""JSON output formatter for machine-readable reports."""
import json
from datetime import datetime, date
from dataclasses import asdict
from typing import List, Dict, Any

from commodity_pipeline.models import (
    Commodity, TechnicalSignals, TrendDirection,
    OptionContract, NewsItem, StrategyRecommendation
)


class JSONOutput:
    """Format pipeline results as JSON."""

    def _serialize_value(self, obj: Any) -> Any:
        """Convert non-serializable objects to JSON-compatible types."""
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, TrendDirection):
            return obj.value
        if isinstance(obj, float) and (obj == float("inf") or obj == float("-inf")):
            return str(obj)  # JSON doesn't support infinity
        return obj

    def _serialize_dataclass(self, obj: Any) -> dict:
        """Recursively serialize a dataclass to dict."""
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field in obj.__dataclass_fields__:
                value = getattr(obj, field)
                result[field] = self._serialize_value(value)
            return result
        return obj

    def to_dict(
        self,
        commodities: List[Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]],
        strategies: Dict[str, List[StrategyRecommendation]],
        alerts: List[NewsItem]
    ) -> dict:
        """Convert all data to a serializable dict."""
        result = {
            "generated_at": datetime.now().isoformat(),
            "commodities": [],
            "alerts": []
        }

        # Process each commodity
        for c in commodities:
            code = c.code
            commodity_data = {
                "code": c.code,
                "name": c.name,
                "exchange": c.exchange,
                "main_contract": c.main_contract,
                "price": c.price,
                "change_1d": c.change_1d,
                "change_3d": c.change_3d,
                "change_5d": c.change_5d,
                "technical": None,
                "options": [],
                "news": [],
                "strategies": []
            }

            # Technical signals
            if code in technical:
                tech = technical[code]
                commodity_data["technical"] = {
                    "commodity_code": tech.commodity_code,
                    "ma_signal": tech.ma_signal,
                    "macd_signal": tech.macd_signal,
                    "rsi_value": tech.rsi_value,
                    "rsi_signal": tech.rsi_signal,
                    "boll_position": tech.boll_position,
                    "kdj_signal": tech.kdj_signal,
                    "atr_value": tech.atr_value,
                    "obv_trend": tech.obv_trend,
                    "cci_signal": tech.cci_signal,
                    "overall_trend": tech.overall_trend.value,
                    "strength": tech.strength
                }

            # Options
            if code in options:
                for opt in options[code]:
                    commodity_data["options"].append({
                        "code": opt.code,
                        "underlying": opt.underlying,
                        "strike": opt.strike,
                        "expiry": opt.expiry.isoformat(),
                        "option_type": opt.option_type,
                        "market_price": opt.market_price,
                        "volume": opt.volume,
                        "iv": opt.iv,
                        "delta": opt.delta,
                        "gamma": opt.gamma,
                        "theta": opt.theta,
                        "vega": opt.vega,
                        "rho": opt.rho,
                        "bs_value": opt.bs_value,
                        "mispricing": opt.mispricing
                    })

            # News
            if code in news:
                for n in news[code]:
                    commodity_data["news"].append({
                        "title": n.title,
                        "source": n.source,
                        "url": n.url,
                        "published": n.published.isoformat(),
                        "summary": n.summary,
                        "sentiment": n.sentiment
                    })

            # Strategies
            if code in strategies:
                for s in strategies[code]:
                    commodity_data["strategies"].append({
                        "name": s.name,
                        "type": s.type,
                        "legs": s.legs,
                        "max_profit": self._serialize_value(s.max_profit),
                        "max_loss": s.max_loss,
                        "breakeven": s.breakeven,
                        "rationale": s.rationale,
                        "confidence": s.confidence
                    })

            result["commodities"].append(commodity_data)

        # Alerts
        for alert in alerts:
            result["alerts"].append({
                "title": alert.title,
                "source": alert.source,
                "url": alert.url,
                "published": alert.published.isoformat(),
                "summary": alert.summary,
                "sentiment": alert.sentiment
            })

        return result

    def to_json(
        self,
        commodities: List[Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]],
        strategies: Dict[str, List[StrategyRecommendation]],
        alerts: List[NewsItem],
        indent: int = 2
    ) -> str:
        """Convert to JSON string."""
        data = self.to_dict(commodities, technical, options, news, strategies, alerts)
        return json.dumps(data, indent=indent, ensure_ascii=False)

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
        """Save JSON report to file."""
        content = self.to_json(commodities, technical, options, news, strategies, alerts)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
