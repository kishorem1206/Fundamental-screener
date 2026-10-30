"""Every series on the Market & Macro page: what it is and where it comes from."""
from __future__ import annotations

_MOSPI = "MoSPI"
_RBI = "RBI (rbi.org.in, current rates)"
_YAHOO = "Yahoo Finance"
_NSDL = "NSDL FPI"
_NSE = "NSE index file"

# id: (label, unit, group, source, frequency)
SERIES: dict[str, tuple[str, str, str, str, str]] = {
    "gdp_growth_q": ("Real GDP growth, latest quarter", "% yoy", "Growth", f"{_MOSPI} national accounts (constant prices)", "quarterly"),
    "gdp_growth_a": ("Real GDP growth, financial year", "% yoy", "Growth", f"{_MOSPI} national accounts (constant prices)", "annual"),
    "iip_growth": ("Industrial production (IIP)", "% yoy", "Growth", f"{_MOSPI} IIP, General", "monthly"),
    "cpi_inflation": ("Consumer inflation (CPI)", "% yoy", "Prices", f"{_MOSPI} CPI, All India Combined (2012 base to 2025, 2024 base from 2026)", "monthly"),
    "wpi_inflation": ("Wholesale inflation (WPI)", "% yoy", "Prices", f"{_MOSPI} WPI, all commodities", "monthly"),
    "repo": ("Policy repo rate", "%", "Rates and liquidity", _RBI, "on change"),
    "sdf": ("Standing deposit facility", "%", "Rates and liquidity", _RBI, "on change"),
    "msf": ("Marginal standing facility", "%", "Rates and liquidity", _RBI, "on change"),
    "crr": ("Cash reserve ratio", "%", "Rates and liquidity", _RBI, "on change"),
    "slr": ("Statutory liquidity ratio", "%", "Rates and liquidity", _RBI, "on change"),
    "call_rate": ("Call money rate, top of range", "%", "Rates and liquidity", _RBI, "daily"),
    "gsec_10y": ("10-year government yield", "%", "Rates and liquidity", _RBI, "daily"),
    "usd_inr": ("Rupee per dollar", "₹", "Currency", f"{_RBI}, FBIL reference rate", "daily"),
    "fx_reserves": ("Foreign exchange reserves", "$ bn", "Currency", f"{_MOSPI} RBI dataset", "monthly"),
    "nifty_pe": ("Nifty 50 P/E", "x", "Market", _NSE, "daily"),
    "nifty_pb": ("Nifty 50 P/B", "x", "Market", _NSE, "daily"),
    "nifty_yield": ("Nifty 50 dividend yield", "%", "Market", _NSE, "daily"),
    "india_vix": ("India VIX", "", "Market", _NSE, "daily"),
    "cboe_vix": ("CBOE VIX (US)", "", "Global", "CBOE", "daily"),
    "us_10y": ("US 10-year yield", "%", "Global", _YAHOO, "daily"),
    "dollar_index": ("Dollar index", "", "Global", _YAHOO, "daily"),
    "brent": ("Brent crude", "$", "Global", _YAHOO, "daily"),
    "gold": ("Gold", "$/oz", "Global", _YAHOO, "daily"),
    "wb_gdp_growth": ("India GDP growth, long run", "%", "Long run", "World Bank", "annual"),
    "wb_inflation": ("India inflation, long run", "%", "Long run", "World Bank", "annual"),
    "fpi_equity_daily": ("FPI equity, daily net", "₹ cr", "FPI flows", _NSDL, "daily"),
    "fpi_debt_daily": ("FPI debt, daily net", "₹ cr", "FPI flows", _NSDL, "daily"),
    "fpi_equity_month": ("FPI equity, monthly net", "₹ cr", "FPI flows", _NSDL, "monthly"),
    "fpi_debt_month": ("FPI debt, monthly net", "₹ cr", "FPI flows", _NSDL, "monthly"),
}
GROUPS = ["Growth", "Prices", "Rates and liquidity", "Currency", "Market", "FPI flows", "Global", "Long run"]
