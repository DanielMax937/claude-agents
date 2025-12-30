"""Parser utilities for option codes and holdings."""
import re
from typing import List, Dict, Any
from datetime import datetime


def parse_option_code(code: str) -> Dict[str, Any]:
    """
    Parse Chinese futures option code into components.

    Format examples:
        CU2501-C-75000  -> Copper Jan 2025, 75000 strike, Call
        CU2501P73000     -> Copper Jan 2025, 73000 strike, Put (compact format)
        rb2505-c-3500    -> Rebar May 2025, 3500 strike, Call

    Returns:
        Dict with keys: symbol, expiry, strike, type, raw_code
    """
    if not code or not isinstance(code, str):
        raise ValueError(f"Invalid option code format: {code}")

    # Pattern: SYMBOL(1-4 chars) + YYMM (year-month) + [M?] + [-]? + [CP] + [-]? + STRIKE
    pattern = r"^([A-Za-z]{1,4})(\d{4})M?[-_]?([CP])[-_]?(\d+)$"
    match = re.match(pattern, code.replace(" ", "").upper())

    if not match:
        # Try alternate format with dash separator
        pattern2 = r"^([A-Za-z]{1,4})(\d{4})M?[-_]([CP])[-_](\d+)$"
        match = re.match(pattern2, code.replace(" ", "").upper())

    if not match:
        raise ValueError(f"Invalid option code format: {code}")

    symbol = match.group(1).upper()
    year_month = match.group(2)
    type_char = match.group(3).upper()
    strike = float(match.group(4))

    # Parse YYMM into YYYY-MM
    year_int = int(year_month[:2])
    month_int = int(year_month[2:4])

    # Assume 20xx for years 00-50, 19xx for 51-99
    if year_int <= 50:
        year_int += 2000
    else:
        year_int += 1900

    # Handle year rollover - if month is in past, assume next cycle
    current_year = datetime.now().year
    if year_int < current_year:
        # Could be next cycle - add 4 years (typical futures cycle)
        year_int += 4

    expiry = f"{year_int}-{month_int:02d}"

    return {
        "symbol": symbol,
        "expiry": expiry,
        "strike": strike,
        "type": "call" if type_char == "C" else "put",
        "raw_code": code
    }


def parse_holdings(holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse and enrich a list of holdings with parsed option data.

    Args:
        holdings: List of dicts with at least 'code' key

    Returns:
        Enriched list with symbol, strike, type, expiry added to each dict
    """
    result = []

    for holding in holdings:
        if "code" not in holding:
            raise ValueError(f"Holding missing 'code' key: {holding}")

        parsed = parse_option_code(holding["code"])

        # Merge parsed data with original holding
        enriched = {**holding, **parsed}
        result.append(enriched)

    return result
