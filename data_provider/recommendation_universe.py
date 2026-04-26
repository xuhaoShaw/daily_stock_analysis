# -*- coding: utf-8 -*-
"""Default recommendation universes for markets without a free full-market screener."""

from __future__ import annotations

from typing import Dict, List


CN_ETF_UNIVERSE: List[Dict[str, str]] = [
    {"code": "510300", "name": "沪深300ETF", "asset_type": "etf"},
    {"code": "510500", "name": "中证500ETF", "asset_type": "etf"},
    {"code": "510050", "name": "上证50ETF", "asset_type": "etf"},
    {"code": "159915", "name": "创业板ETF", "asset_type": "etf"},
    {"code": "588000", "name": "科创50ETF", "asset_type": "etf"},
    {"code": "512100", "name": "中证1000ETF", "asset_type": "etf"},
    {"code": "512880", "name": "证券ETF", "asset_type": "etf"},
    {"code": "512480", "name": "半导体ETF", "asset_type": "etf"},
    {"code": "515790", "name": "光伏ETF", "asset_type": "etf"},
    {"code": "516160", "name": "新能源ETF", "asset_type": "etf"},
    {"code": "513100", "name": "纳指ETF", "asset_type": "etf"},
    {"code": "513500", "name": "标普500ETF", "asset_type": "etf"},
    {"code": "159941", "name": "纳指ETF", "asset_type": "etf"},
    {"code": "159920", "name": "恒生ETF", "asset_type": "etf"},
    {"code": "518880", "name": "黄金ETF", "asset_type": "etf"},
    {"code": "159985", "name": "豆粕ETF", "asset_type": "etf"},
]

US_STOCK_UNIVERSE: List[Dict[str, str]] = [
    {"code": "AAPL", "name": "Apple", "asset_type": "stock"},
    {"code": "MSFT", "name": "Microsoft", "asset_type": "stock"},
    {"code": "NVDA", "name": "NVIDIA", "asset_type": "stock"},
    {"code": "AMZN", "name": "Amazon", "asset_type": "stock"},
    {"code": "META", "name": "Meta Platforms", "asset_type": "stock"},
    {"code": "GOOGL", "name": "Alphabet Class A", "asset_type": "stock"},
    {"code": "GOOG", "name": "Alphabet Class C", "asset_type": "stock"},
    {"code": "TSLA", "name": "Tesla", "asset_type": "stock"},
    {"code": "AVGO", "name": "Broadcom", "asset_type": "stock"},
    {"code": "AMD", "name": "Advanced Micro Devices", "asset_type": "stock"},
    {"code": "NFLX", "name": "Netflix", "asset_type": "stock"},
    {"code": "JPM", "name": "JPMorgan Chase", "asset_type": "stock"},
    {"code": "BAC", "name": "Bank of America", "asset_type": "stock"},
    {"code": "XOM", "name": "Exxon Mobil", "asset_type": "stock"},
    {"code": "CVX", "name": "Chevron", "asset_type": "stock"},
    {"code": "COST", "name": "Costco", "asset_type": "stock"},
    {"code": "WMT", "name": "Walmart", "asset_type": "stock"},
    {"code": "HD", "name": "Home Depot", "asset_type": "stock"},
    {"code": "UNH", "name": "UnitedHealth", "asset_type": "stock"},
    {"code": "ORCL", "name": "Oracle", "asset_type": "stock"},
    {"code": "CRM", "name": "Salesforce", "asset_type": "stock"},
    {"code": "ADBE", "name": "Adobe", "asset_type": "stock"},
    {"code": "QCOM", "name": "Qualcomm", "asset_type": "stock"},
    {"code": "MU", "name": "Micron", "asset_type": "stock"},
    {"code": "INTC", "name": "Intel", "asset_type": "stock"},
    {"code": "UBER", "name": "Uber", "asset_type": "stock"},
    {"code": "PLTR", "name": "Palantir", "asset_type": "stock"},
    {"code": "COIN", "name": "Coinbase", "asset_type": "stock"},
    {"code": "MSTR", "name": "Strategy", "asset_type": "stock"},
    {"code": "SMCI", "name": "Super Micro Computer", "asset_type": "stock"},
]

US_ETF_UNIVERSE: List[Dict[str, str]] = [
    {"code": "SPY", "name": "SPDR S&P 500 ETF", "asset_type": "etf"},
    {"code": "QQQ", "name": "Invesco QQQ Trust", "asset_type": "etf"},
    {"code": "VOO", "name": "Vanguard S&P 500 ETF", "asset_type": "etf"},
    {"code": "IVV", "name": "iShares Core S&P 500 ETF", "asset_type": "etf"},
    {"code": "IWM", "name": "iShares Russell 2000 ETF", "asset_type": "etf"},
    {"code": "DIA", "name": "SPDR Dow Jones Industrial Average ETF", "asset_type": "etf"},
    {"code": "VTI", "name": "Vanguard Total Stock Market ETF", "asset_type": "etf"},
    {"code": "SCHD", "name": "Schwab US Dividend Equity ETF", "asset_type": "etf"},
    {"code": "XLK", "name": "Technology Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLF", "name": "Financial Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLE", "name": "Energy Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLY", "name": "Consumer Discretionary Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLV", "name": "Health Care Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLI", "name": "Industrial Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLP", "name": "Consumer Staples Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "XLU", "name": "Utilities Select Sector SPDR Fund", "asset_type": "etf"},
    {"code": "SMH", "name": "VanEck Semiconductor ETF", "asset_type": "etf"},
    {"code": "SOXX", "name": "iShares Semiconductor ETF", "asset_type": "etf"},
    {"code": "ARKK", "name": "ARK Innovation ETF", "asset_type": "etf"},
    {"code": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "asset_type": "etf"},
    {"code": "HYG", "name": "iShares iBoxx High Yield Corporate Bond ETF", "asset_type": "etf"},
    {"code": "GLD", "name": "SPDR Gold Shares", "asset_type": "etf"},
    {"code": "SLV", "name": "iShares Silver Trust", "asset_type": "etf"},
    {"code": "USO", "name": "United States Oil Fund", "asset_type": "etf"},
    {"code": "BITO", "name": "ProShares Bitcoin Strategy ETF", "asset_type": "etf"},
]


def get_recommendation_universe(market: str, asset_type: str = "stock") -> List[Dict[str, str]]:
    """Return a stable seed universe for recommendation discovery."""
    normalized_market = (market or "").strip().lower()
    normalized_asset_type = (asset_type or "stock").strip().lower()
    if normalized_market == "cn":
        if normalized_asset_type in {"etf", "all"}:
            return list(CN_ETF_UNIVERSE)
        return []
    if normalized_market != "us":
        return []
    if normalized_asset_type == "stock":
        return list(US_STOCK_UNIVERSE)
    if normalized_asset_type == "etf":
        return list(US_ETF_UNIVERSE)
    if normalized_asset_type == "all":
        return list(US_STOCK_UNIVERSE) + list(US_ETF_UNIVERSE)
    return []
