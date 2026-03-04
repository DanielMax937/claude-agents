"""Wrapper for china-futures skill.

The china-futures skill provides access to Chinese commodity futures and options
data from a local Django API server (http://127.0.0.1:8000/polls/).

Endpoints used:
- /good/list: Get all commodities with main contract info
- /detail/{code}/{contract_no}: Get OHLCV history for a contract
- /preview: Get market preview with top gainers/losers
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from commodity_pipeline.models import Commodity, OHLCVBar
from commodity_pipeline.skills.base import BaseSkillWrapper, SkillError
from skill_wrapper import SkillOutputFormat


class ChinaFuturesSkill(BaseSkillWrapper):
    """Wrapper for china-futures Claude Code skill.

    Provides access to Chinese commodity futures data via CLI skill scripts
    that call a local Django API server.
    """

    @property
    def skill_name(self) -> str:
        return "china-futures"

    def get_main_contracts(self) -> List[Commodity]:
        """Get all main contracts for commodities with price changes.

        Uses futures_quote script without symbol argument to get all main contracts.
        Returns list of Commodity dataclass instances.
        """
        # Use futures_quote with --main --json flags, longer timeout
        result = self._run("futures_quote", args="--main --json",
                          output_format=SkillOutputFormat.JSON, timeout=300)
        commodities = []
        for c in result.output or []:
            commodities.append(Commodity(
                code=c.get("code", c.get("symbol", "").rstrip("0123456789")),
                name=c.get("name", ""),
                exchange=c.get("exchange", ""),
                main_contract=c.get("symbol", ""),
                price=float(c.get("price", 0) or 0),
                change_1d=float(c.get("change_1d", c.get("pct_change", 0)) or 0),
                change_3d=float(c.get("change_3d", 0) or 0),
                change_5d=float(c.get("change_5d", 0) or 0)
            ))
        return commodities

    def get_quote(self, symbol: str, contract: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a single commodity.

        Args:
            symbol: Commodity code (e.g., 'CU', 'AU')
            contract: Optional contract number (e.g., '2503'). If None, uses main contract.

        Returns:
            Dict with quote data including price, OHLC, volume, pct_change, etc.
        """
        args = f"{symbol} --json"
        if contract:
            args = f"{symbol} --contract {contract} --json"

        result = self._run("futures_quote", args=args,
                          output_format=SkillOutputFormat.JSON, timeout=60)
        return result.output

    def get_market_preview(self) -> Optional[Dict[str, Any]]:
        """Get market preview with top gainers and losers.

        Returns:
            Dict with keys: total (market stats), upperTop3 (gainers), downTop3 (losers)
        """
        result = self._run("futures_quote", args="--preview --json",
                          output_format=SkillOutputFormat.JSON, timeout=60)
        return result.output

    def get_ohlcv(self, symbol: str, contract: Optional[str] = None,
                  days: int = 15) -> List[OHLCVBar]:
        """Get OHLCV historical data for a contract.

        Args:
            symbol: Commodity code (e.g., 'CU', 'AU')
            contract: Optional contract number (e.g., '2503'). If None, uses main contract.
            days: Number of recent days to return (default: 15)

        Returns:
            List of OHLCVBar dataclass instances with OHLCV data.
        """
        # Build args: symbol is positional, --contract is optional
        args = f"{symbol} --days {days} --json"
        if contract:
            args = f"{symbol} --contract {contract} --days {days} --json"

        result = self._run("futures_history", args=args,
                          output_format=SkillOutputFormat.JSON, timeout=60)

        bars = []
        for bar in result.output or []:
            bar_date = bar.get("date", "")
            if isinstance(bar_date, str) and bar_date:
                bar_date = datetime.strptime(bar_date[:10], "%Y-%m-%d").date()

            bars.append(OHLCVBar(
                date=bar_date,
                open=float(bar.get("open", 0)),
                high=float(bar.get("high", 0)),
                low=float(bar.get("low", 0)),
                close=float(bar.get("close", 0)),
                volume=int(bar.get("volume", 0))
            ))
        return bars

    def get_history(self, symbol: str, contract: Optional[str] = None,
                    days: int = 15) -> List[OHLCVBar]:
        """Alias for get_ohlcv for backward compatibility."""
        return self.get_ohlcv(symbol, contract, days)

    def get_options_chain(self, underlying: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        """Get options chain for a commodity.

        Args:
            underlying: Underlying commodity code (e.g., 'CU', 'AU')
            expiry: Optional expiry contract (e.g., '2503')

        Returns:
            Dict with chain data including 'chain' list of strikes with calls/puts.
        """
        args = f"{underlying} --json"
        if expiry:
            args = f"{underlying} --expiry {expiry} --json"

        result = self._run("options_chain", args=args,
                          output_format=SkillOutputFormat.JSON, timeout=60)
        return result.output or {}

    def get_options_list(self, underlying: str, expiry: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get flat list of all options for a commodity.

        Args:
            underlying: Underlying commodity code (e.g., 'CU', 'AU')
            expiry: Optional expiry contract (e.g., '2503')

        Returns:
            List of option contracts with code, strike, type, prices, Greeks, etc.
        """
        # options_list uses --underlying/-u flag, not positional
        args = f"list --underlying {underlying} --json"
        if expiry:
            args = f"list --underlying {underlying} --expiry {expiry} --json"

        result = self._run("options_list", args=args,
                          output_format=SkillOutputFormat.JSON, timeout=600)
        # options_list returns list directly when --json is used
        return result.output if isinstance(result.output, list) else []

    def get_options_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote for a specific options contract.

        Args:
            symbol: Option contract code (e.g., 'CU2503C58000')

        Returns:
            Dict with option data including prices, Greeks, IV, OI, etc.
        """
        result = self._run("options_quote", args=f"{symbol} --json",
                          output_format=SkillOutputFormat.JSON, timeout=60)
        return result.output

    def get_options_by_underlying(self, underlying: str, expiry: Optional[str] = None,
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """Get all options for an underlying, sorted by volume.

        Args:
            underlying: Underlying commodity code (e.g., 'CU', 'AU')
            expiry: Optional expiry contract (e.g., '2503')
            limit: Maximum number of options to return (default: 50)

        Returns:
            List of option contracts sorted by volume.
        """
        args = f"--underlying {underlying} --limit {limit} --json"
        if expiry:
            args = f"--underlying {underlying} --expiry {expiry} --limit {limit} --json"

        result = self._run("options_quote", args=args,
                          output_format=SkillOutputFormat.JSON, timeout=60)
        return result.output if isinstance(result.output, list) else []
