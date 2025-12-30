"""Strategy stage - Step 10: Generate trading strategy recommendations."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import (
    Commodity, TechnicalSignals, TrendDirection,
    OptionContract, NewsItem, StrategyRecommendation
)
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class StrategyStage:
    """Generate trading strategy recommendations based on all analysis."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def run(
        self,
        commodities: List[Commodity],
        technical: Dict[str, TechnicalSignals],
        options: Dict[str, List[OptionContract]],
        news: Dict[str, List[NewsItem]]
    ) -> Dict[str, List[StrategyRecommendation]]:
        """Generate strategies for all commodities in parallel."""
        logger.info(f"Generating strategies for {len(commodities)} commodities")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self._generate_for_commodity,
                    commodity,
                    technical.get(commodity.code),
                    options.get(commodity.code, []),
                    news.get(commodity.code, [])
                )
                for commodity in commodities
            ]
            results = await asyncio.gather(*tasks)

        return {
            commodities[i].code: results[i]
            for i in range(len(commodities))
        }

    def _generate_for_commodity(
        self,
        commodity: Commodity,
        technical: Optional[TechnicalSignals],
        options: List[OptionContract],
        news: List[NewsItem]
    ) -> List[StrategyRecommendation]:
        """Generate strategies for a single commodity."""
        logger.info(f"Generating strategies for {commodity.code}")

        strategies = []

        # Determine market bias
        trend = technical.overall_trend if technical else TrendDirection.NEUTRAL
        strength = technical.strength if technical else 5

        # Count news sentiment
        positive_news = sum(1 for n in news if n.sentiment == "positive")
        negative_news = sum(1 for n in news if n.sentiment == "negative")
        sentiment_bias = positive_news - negative_news

        # Generate appropriate strategies based on trend
        if trend == TrendDirection.BULLISH:
            strategies.extend(self._bullish_strategies(commodity, options, strength, sentiment_bias))
        elif trend == TrendDirection.BEARISH:
            strategies.extend(self._bearish_strategies(commodity, options, strength, sentiment_bias))
        else:
            strategies.extend(self._neutral_strategies(commodity, options, strength))

        # Limit to 3+ recommendations
        if len(strategies) < 3:
            strategies.extend(self._filler_strategies(commodity, options))

        logger.info(f"Generated {len(strategies)} strategies for {commodity.code}")
        return strategies[:5]  # Cap at 5

    def _bullish_strategies(
        self,
        commodity: Commodity,
        options: List[OptionContract],
        strength: int,
        sentiment_bias: int
    ) -> List[StrategyRecommendation]:
        """Generate bullish strategies."""
        strategies = []

        # Find call options
        calls = [o for o in options if o.option_type == "call"]
        call = calls[0] if calls else None

        # Long Call - basic bullish play
        if call:
            confidence = min(10, strength + (1 if sentiment_bias > 0 else 0))
            strategies.append(StrategyRecommendation(
                name="Long Call",
                type="directional",
                legs=[{"action": "buy", "option": call.code, "quantity": 1}],
                max_profit=float("inf"),
                max_loss=call.market_price,
                breakeven=[call.strike + call.market_price],
                rationale=f"Bullish on {commodity.name} with strength {strength}/10. "
                         f"Delta {call.delta:.2f} provides leveraged upside exposure.",
                confidence=confidence
            ))

        # Bull Call Spread - if we have multiple strikes
        if len(calls) >= 2:
            lower_call = min(calls, key=lambda x: x.strike)
            higher_call = max(calls, key=lambda x: x.strike)
            net_debit = lower_call.market_price - higher_call.market_price

            strategies.append(StrategyRecommendation(
                name="Bull Call Spread",
                type="directional",
                legs=[
                    {"action": "buy", "option": lower_call.code, "quantity": 1},
                    {"action": "sell", "option": higher_call.code, "quantity": 1}
                ],
                max_profit=higher_call.strike - lower_call.strike - net_debit,
                max_loss=net_debit,
                breakeven=[lower_call.strike + net_debit],
                rationale=f"Limited risk bullish play on {commodity.name}. "
                         f"Caps upside but reduces cost basis.",
                confidence=min(10, strength)
            ))

        return strategies

    def _bearish_strategies(
        self,
        commodity: Commodity,
        options: List[OptionContract],
        strength: int,
        sentiment_bias: int
    ) -> List[StrategyRecommendation]:
        """Generate bearish strategies."""
        strategies = []

        # Find put options
        puts = [o for o in options if o.option_type == "put"]
        put = puts[0] if puts else None

        # Long Put - basic bearish play
        if put:
            confidence = min(10, strength + (1 if sentiment_bias < 0 else 0))
            strategies.append(StrategyRecommendation(
                name="Long Put",
                type="directional",
                legs=[{"action": "buy", "option": put.code, "quantity": 1}],
                max_profit=put.strike - put.market_price,
                max_loss=put.market_price,
                breakeven=[put.strike - put.market_price],
                rationale=f"Bearish on {commodity.name} with strength {strength}/10. "
                         f"Delta {put.delta:.2f} provides downside exposure.",
                confidence=confidence
            ))

        # Bear Put Spread
        if len(puts) >= 2:
            higher_put = max(puts, key=lambda x: x.strike)
            lower_put = min(puts, key=lambda x: x.strike)
            net_debit = higher_put.market_price - lower_put.market_price

            strategies.append(StrategyRecommendation(
                name="Bear Put Spread",
                type="directional",
                legs=[
                    {"action": "buy", "option": higher_put.code, "quantity": 1},
                    {"action": "sell", "option": lower_put.code, "quantity": 1}
                ],
                max_profit=higher_put.strike - lower_put.strike - net_debit,
                max_loss=net_debit,
                breakeven=[higher_put.strike - net_debit],
                rationale=f"Limited risk bearish play on {commodity.name}. "
                         f"Caps downside profit but reduces cost.",
                confidence=min(10, strength)
            ))

        return strategies

    def _neutral_strategies(
        self,
        commodity: Commodity,
        options: List[OptionContract],
        strength: int
    ) -> List[StrategyRecommendation]:
        """Generate neutral/volatility strategies."""
        strategies = []

        calls = [o for o in options if o.option_type == "call"]
        puts = [o for o in options if o.option_type == "put"]

        # Iron Condor for range-bound markets
        if calls and puts:
            call = calls[0]
            put = puts[0]

            strategies.append(StrategyRecommendation(
                name="Short Straddle",
                type="income",
                legs=[
                    {"action": "sell", "option": call.code, "quantity": 1},
                    {"action": "sell", "option": put.code, "quantity": 1}
                ],
                max_profit=call.market_price + put.market_price,
                max_loss=float("inf"),
                breakeven=[
                    put.strike - (call.market_price + put.market_price),
                    call.strike + (call.market_price + put.market_price)
                ],
                rationale=f"Neutral view on {commodity.name}. "
                         f"Collect premium if price stays range-bound.",
                confidence=5
            ))

        return strategies

    def _filler_strategies(
        self,
        commodity: Commodity,
        options: List[OptionContract]
    ) -> List[StrategyRecommendation]:
        """Generate filler strategies to meet minimum count."""
        strategies = []

        # Cash-secured position (conceptual)
        strategies.append(StrategyRecommendation(
            name="Wait and Watch",
            type="neutral",
            legs=[],
            max_profit=0,
            max_loss=0,
            breakeven=[commodity.price],
            rationale=f"No clear signal for {commodity.name}. "
                     f"Consider monitoring for clearer entry.",
            confidence=3
        ))

        return strategies
