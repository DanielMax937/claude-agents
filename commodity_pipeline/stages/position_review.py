"""Position Review Stage - evaluates user's existing options positions."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import (
    Commodity, TechnicalSignals, TrendDirection,
    OptionContract, NewsItem
)
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class PositionReviewStage:
    """Analyze user's options holdings and generate recommendations."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def run(
        self,
        holdings: List[Dict[str, Any]],
        commodities: Dict[str, Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze all positions and generate recommendations.

        Args:
            holdings: List of position dicts (enriched by parser)
            commodities: Dict mapping symbol to Commodity
            technical: Dict mapping symbol to TechnicalSignals
            options: Dict mapping symbol to list of OptionContract
            news: Dict mapping symbol to list of NewsItem

        Returns:
            List of position analysis dicts with scores and recommendations
        """
        logger.info(f"Starting position review for {len(holdings)} holdings")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self._analyze_one,
                    holding,
                    commodities,
                    technical,
                    options,
                    news
                )
                for holding in holdings
            ]
            results = await asyncio.gather(*tasks)

        logger.info(f"Position review complete for {len(results)} positions")
        return results

    def _analyze_one(
        self,
        holding: Dict[str, Any],
        commodities: Dict[str, Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]]
    ) -> Dict[str, Any]:
        """Analyze a single position."""
        symbol = holding["symbol"]
        code = holding["code"]

        logger.debug(f"Analyzing position {code}")

        # Get relevant data
        commodity = commodities.get(symbol)
        tech_signals = technical.get(symbol)
        news_list = news.get(symbol, [])

        # Find matching option contract for current Greeks
        option_contract = self._find_option_contract(
            code, options.get(symbol, [])
        )

        if not option_contract:
            logger.warning(f"No option contract found for {code}")
            return self._missing_data_response(holding)

        spot = commodity.price if commodity else 0
        trend = tech_signals.overall_trend.value if tech_signals else "neutral"

        # Score each dimension
        greeks_score = self._score_greeks(holding, option_contract, spot, trend)
        technical_score = self._score_technical(commodity, tech_signals) if commodity else 50
        time_score = self._score_time(holding, option_contract)
        news_score = self._score_news(news_list)

        # Calculate weighted overall score
        weights = self.config.signal_weights
        overall = (
            greeks_score * weights["greeks"] / 100 +
            technical_score * weights["technical"] / 100 +
            time_score * weights["time"] / 100 +
            news_score * weights["news"] / 100
        )

        # Determine signal and recommendation
        signal = self._determine_signal(overall)
        recommendation = self._generate_recommendation(overall, signal)
        confidence = overall / 100

        return {
            "position_code": code,
            "signal": signal,
            "confidence": round(confidence, 2),
            "scores": {
                "greeks": greeks_score,
                "technical": technical_score,
                "time": time_score,
                "news": news_score
            },
            "metrics": self._build_metrics_dict(
                holding, option_contract, spot, tech_signals
            ),
            "recommendation": recommendation,
            "reason": self._generate_reason(
                greeks_score, technical_score, time_score, news_score,
                recommendation, holding, option_contract, spot, trend
            )
        }

    def _find_option_contract(
        self,
        code: str,
        contracts: List[OptionContract]
    ) -> Optional[OptionContract]:
        """Find the option contract matching the holding code."""
        for contract in contracts:
            if contract.code == code:
                return contract
        return None

    def _missing_data_response(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Return response when market data is missing."""
        return {
            "position_code": holding["code"],
            "signal": "neutral",
            "confidence": 0.0,
            "scores": {"greeks": 0, "technical": 0, "time": 0, "news": 0},
            "metrics": {},
            "recommendation": "CLOSE",
            "reason": "Insufficient market data available for analysis"
        }

    def _score_greeks(
        self,
        position_data: Dict[str, Any],
        greeks: OptionContract,
        spot: float,
        trend: str
    ) -> int:
        """Score position based on Greeks alignment with trend."""
        score = 50  # baseline

        option_type = position_data.get("type", "call")
        delta = greeks.delta
        gamma = greeks.gamma
        theta = greeks.theta
        iv = greeks.iv

        # Delta alignment with trend
        if trend == "bullish":
            if option_type == "call" and delta > 0.3:
                score += 20
            elif option_type == "put":
                score -= 30
        elif trend == "bearish":
            if option_type == "put" and delta < -0.3:
                score += 20
            elif option_type == "call":
                score -= 30

        # Gamma risk (high gamma = higher risk)
        if abs(gamma) > 0.00005:  # High gamma for futures
            score -= 15
        elif abs(gamma) < 0.00001:  # Low gamma is good
            score += 10

        # Theta urgency
        days_to_expiry = (greeks.expiry - date.today()).days
        if days_to_expiry < 7:
            score -= 25  # Last week burn
        elif days_to_expiry < 21:
            score -= 10  # Decay zone

        # IV considerations
        if iv > 0.3:  # High IV - expensive
            score -= 10
        elif iv < 0.15:  # Low IV - good value
            score += 10

        return max(0, min(100, score))

    def _score_technical(
        self,
        commodity: Optional[Commodity],
        technical: Optional[TechnicalSignals]
    ) -> int:
        """Score based on technical analysis."""
        if not technical:
            return 50  # neutral baseline

        score = 50

        # Overall trend strength (1-10) contributes heavily
        score += (technical.strength - 5) * 5

        # Trend direction bonus
        if technical.overall_trend == TrendDirection.BULLISH:
            score += 10
        elif technical.overall_trend == TrendDirection.BEARISH:
            score -= 10

        # RSI not overbought/oversold is good
        if 40 <= technical.rsi_value <= 60:
            score += 10
        elif technical.rsi_value > 70:
            score -= 15  # Overbought risk
        elif technical.rsi_value < 30:
            score -= 15  # Oversold bounce opportunity

        # MACD confirmation
        if technical.ma_signal == "buy" and technical.macd_signal == "buy":
            score += 10

        return max(0, min(100, score))

    def _score_time(
        self,
        position_data: Dict[str, Any],
        greeks: OptionContract
    ) -> int:
        """Score based on time to expiry."""
        days_to_expiry = (greeks.expiry - date.today()).days
        score = 50

        # Optimal zone: 30-60 days
        if 30 <= days_to_expiry <= 60:
            score += 30
        elif 21 <= days_to_expiry < 30:
            score += 20
        elif 61 <= days_to_expiry <= 90:
            score += 15

        # Danger zones
        if days_to_expiry < 7:
            score -= 30  # Very urgent
        elif days_to_expiry < 21:
            score -= 15  # Decay accelerating

        # Too much time = capital inefficiency
        if days_to_expiry > 180:
            score -= 10

        return max(0, min(100, score))

    def _score_news(self, news_list: List[NewsItem]) -> int:
        """Score based on news sentiment."""
        if not news_list:
            return 50  # neutral baseline

        score = 50
        positive = sum(1 for n in news_list if n.sentiment == "positive")
        negative = sum(1 for n in news_list if n.sentiment == "negative")
        total = len(news_list)

        if total == 0:
            return 50

        positive_ratio = positive / total
        negative_ratio = negative / total

        # Positive news is good
        score += positive_ratio * 30

        # Negative news is bad
        score -= negative_ratio * 30

        return max(0, min(100, score))

    def _determine_signal(self, overall_score: float) -> str:
        """Determine signal based on overall score."""
        if overall_score >= 65:
            return "bullish"
        elif overall_score <= 40:
            return "bearish"
        else:
            return "neutral"

    def _generate_recommendation(self, overall_score: float, signal: str) -> str:
        """Generate HOLD/ADJUST/CLOSE recommendation."""
        if overall_score >= 65:
            return "HOLD"
        elif overall_score >= 45:
            return "ADJUST"
        else:
            return "CLOSE"

    def _build_metrics_dict(
        self,
        holding: Dict[str, Any],
        greeks: OptionContract,
        spot: float,
        technical: Optional[TechnicalSignals]
    ) -> Dict[str, Any]:
        """Build metrics dict for output."""
        days_to_expiry = (greeks.expiry - date.today()).days

        metrics = {
            "delta": greeks.delta,
            "gamma": greeks.gamma,
            "theta": greeks.theta,
            "vega": greeks.vega,
            "iv": round(greeks.iv * 100, 1),  # As percentage
            "iv_rank": "N/A",  # Would need historical IV data
            "spot": spot,
            "strike": greeks.strike,
            "dte": days_to_expiry,
            "itm_amount": max(0, spot - greeks.strike) if holding["type"] == "call" else max(0, greeks.strike - spot)
        }

        if technical:
            metrics["rsi"] = technical.rsi_value
            metrics["trend"] = technical.overall_trend.value

        return metrics

    def _generate_reason(
        self,
        greeks_score: int,
        technical_score: int,
        time_score: int,
        news_score: int,
        recommendation: str,
        holding: Dict[str, Any],
        greeks: OptionContract,
        spot: float,
        trend: str
    ) -> str:
        """Generate detailed reason explanation."""
        parts = []

        # Greeks explanation
        delta_desc = "Moderate" if 0.3 <= abs(greeks.delta) <= 0.7 else "Low" if abs(greeks.delta) < 0.3 else "High"
        parts.append(f"Greeks: {greeks_score}/100 - {delta_desc} delta exposure")

        # Technical explanation
        if technical_score >= 70:
            parts.append(f"Technical: {technical_score}/100 - Strong {trend} setup")
        elif technical_score <= 40:
            parts.append(f"Technical: {technical_score}/100 - Weak technicals")
        else:
            parts.append(f"Technical: {technical_score}/100 - Mixed signals")

        # Time explanation
        dte = (greeks.expiry - date.today()).days
        if dte < 7:
            parts.append(f"Time: {time_score}/100 - Urgent ({dte} DTE)")
        elif dte < 21:
            parts.append(f"Time: {time_score}/100 - Decay zone ({dte} DTE)")
        else:
            parts.append(f"Time: {time_score}/100 - Optimal ({dte} DTE)")

        # News explanation
        if news_score >= 70:
            parts.append(f"News: {news_score}/100 - Supportive headlines")
        elif news_score <= 40:
            parts.append(f"News: {news_score}/100 - Negative sentiment")
        else:
            parts.append(f"News: {news_score}/100 - Neutral to mixed")

        return ". ".join(parts) + "."
