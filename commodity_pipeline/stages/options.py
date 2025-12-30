"""Options stage - Step 7: Get options chains, calculate Greeks/IV/BS."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict

from commodity_pipeline.config import PipelineConfig
from commodity_pipeline.models import Commodity, OptionContract
from commodity_pipeline.skills.china_futures import ChinaFuturesSkill
from commodity_pipeline.skills.options_skill import OptionsSkill
from commodity_pipeline.logger import get_logger

logger = get_logger(__name__)


class OptionsStage:
    """Get options chains and calculate Greeks/IV/BS for top contracts."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.futures_skill = ChinaFuturesSkill()
        self.options_skill = OptionsSkill()

    async def run(self, commodities: List[Commodity]) -> Dict[str, List[OptionContract]]:
        """Get options data for all commodities in parallel."""
        logger.info(f"Starting options analysis for {len(commodities)} commodities")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, self._process_one, commodity)
                for commodity in commodities
            ]
            results = await asyncio.gather(*tasks)

        # Build dict mapping commodity code to list of options
        return {
            commodities[i].code: results[i]
            for i in range(len(commodities))
        }

    def _process_one(self, commodity: Commodity) -> List[OptionContract]:
        """Process options for a single commodity (runs in thread)."""
        logger.info(f"Getting options for {commodity.code}")

        # Get raw options chain from china-futures skill
        raw_chain = self.futures_skill.get_options_chain(commodity.main_contract)
        logger.debug(f"Got {len(raw_chain)} options for {commodity.code}")

        # Sort by volume and take top N
        sorted_chain = sorted(raw_chain, key=lambda x: x.get("volume", 0), reverse=True)
        top_options = sorted_chain[:self.config.top_options_by_volume]

        # Calculate Greeks, IV, BS for each option
        result = []
        for opt in top_options:
            contract = self._enrich_option(opt, commodity)
            result.append(contract)

        logger.info(f"Processed {len(result)} options for {commodity.code}")
        return result

    def _enrich_option(self, opt: dict, commodity: Commodity) -> OptionContract:
        """Calculate Greeks, IV, and BS value for a single option."""
        strike = opt["strike"]
        expiry_str = opt["expiry"]
        option_type = opt["type"]
        market_price = opt["price"]

        # Parse expiry date
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()

        # Calculate time to expiry in years
        days_to_expiry = (expiry - datetime.now().date()).days
        time_years = max(days_to_expiry / 365.0, 0.001)  # Avoid zero

        # Calculate IV from market price
        iv = self.options_skill.calc_iv(
            spot=commodity.price,
            strike=strike,
            time=time_years,
            rate=self.config.risk_free_rate,
            market_price=market_price,
            option_type=option_type
        )

        # Calculate Greeks using the IV
        greeks = self.options_skill.calc_greeks(
            spot=commodity.price,
            strike=strike,
            time=time_years,
            rate=self.config.risk_free_rate,
            vol=iv if iv > 0 else 0.2,  # Default if IV calc fails
            option_type=option_type
        )

        # Calculate Black-Scholes theoretical value
        bs_value = self.options_skill.calc_bs_price(
            spot=commodity.price,
            strike=strike,
            time=time_years,
            rate=self.config.risk_free_rate,
            vol=iv if iv > 0 else 0.2,
            option_type=option_type
        )

        mispricing = market_price - bs_value

        return OptionContract(
            code=opt["code"],
            underlying=commodity.code,
            strike=strike,
            expiry=expiry,
            option_type=option_type,
            market_price=market_price,
            volume=opt.get("volume", 0),
            iv=iv,
            delta=greeks.get("delta", 0.0),
            gamma=greeks.get("gamma", 0.0),
            theta=greeks.get("theta", 0.0),
            vega=greeks.get("vega", 0.0),
            rho=greeks.get("rho", 0.0),
            bs_value=bs_value,
            mispricing=mispricing
        )
