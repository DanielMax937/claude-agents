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

        # Get options list from china-futures skill (use flat list for easier processing)
        raw_options = self.futures_skill.get_options_list(commodity.code)
        logger.debug(f"Got {len(raw_options)} options for {commodity.code}")

        # Sort by volume and take top N
        sorted_options = sorted(raw_options, key=lambda x: x.get("volume", 0), reverse=True)
        top_options = sorted_options[:self.config.top_options_by_volume]

        # Calculate Greeks, IV, BS for each option
        result = []
        for opt in top_options:
            try:
                contract = self._enrich_option(opt, commodity)
                result.append(contract)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping option due to error: {e}")
                continue

        logger.info(f"Processed {len(result)} options for {commodity.code}")
        return result

    def _enrich_option(self, opt: dict, commodity: Commodity) -> OptionContract:
        """Calculate Greeks, IV, and BS value for a single option."""
        # Handle field name variations from API
        strike = opt.get("strike") or opt.get("strike_price", 0)
        expiry_str = opt.get("expiry") or opt.get("expiry_date", "")
        option_type = opt.get("type") or opt.get("option_type", "call")
        market_price = opt.get("price") or opt.get("close_price", 0)

        # Parse expiry date - handle various formats
        if isinstance(expiry_str, str) and expiry_str:
            if len(expiry_str) == 4:  # Format: "2503"
                expiry = datetime.strptime(f"20{expiry_str}", "%Y%m").date()
            elif "-" in expiry_str:  # Format: "2025-03-01"
                expiry = datetime.strptime(expiry_str[:10], "%Y-%m-%d").date()
            else:  # Format: "20250301"
                expiry = datetime.strptime(expiry_str[:8], "%Y%m%d").date()
        else:
            expiry = datetime.now().date()

        # Calculate time to expiry in years
        days_to_expiry = (expiry - datetime.now().date()).days
        time_years = max(days_to_expiry / 365.0, 0.001)  # Avoid zero

        # Use IV from API if available, otherwise calculate from market price
        iv = opt.get("implied_volatility", 0) or opt.get("iv", 0)
        if not iv and market_price > 0:
            iv = self.options_skill.calc_iv(
                spot=commodity.price,
                strike=strike,
                time=time_years,
                rate=self.config.risk_free_rate,
                market_price=market_price,
                option_type=option_type
            )

        # Default volatility if IV calculation fails
        vol = iv / 100 if iv > 1 else iv  # Normalize if percentage
        vol = vol if vol > 0 else 0.2

        # Use Greeks from API if available, otherwise calculate
        if opt.get("delta") is not None:
            greeks = {
                "delta": opt.get("delta", 0),
                "gamma": opt.get("gamma", 0),
                "theta": opt.get("theta", 0),
                "vega": opt.get("vega", 0),
                "rho": opt.get("rho", 0),
            }
        else:
            greeks = self.options_skill.calc_greeks(
                spot=commodity.price,
                strike=strike,
                time=time_years,
                rate=self.config.risk_free_rate,
                vol=vol,
                option_type=option_type
            )

        # Calculate Black-Scholes theoretical value
        bs_value = self.options_skill.calc_bs_price(
            spot=commodity.price,
            strike=strike,
            time=time_years,
            rate=self.config.risk_free_rate,
            vol=vol,
            option_type=option_type
        )

        mispricing = market_price - bs_value if market_price > 0 else 0

        return OptionContract(
            code=opt.get("code") or opt.get("option_code", ""),
            underlying=commodity.code,
            strike=strike,
            expiry=expiry,
            option_type=option_type.lower() if isinstance(option_type, str) else option_type,
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
