from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from .config import get_settings
from .database_queries import get_client_portfolio, query_db, search_market_data
from .rag import get_policy_retriever_chain


def _format_currency(value: float) -> str:
    return f"₹{value:,.0f}"


@tool
def portfolio_lookup(client_id: str) -> str:
    """Lookup a client's portfolio holdings, allocation, and risk profile."""
    portfolio = get_client_portfolio(client_id)
    if not portfolio:
        available = [r["client_id"] for r in query_db("SELECT client_id FROM clients")]
        return f"Client {client_id} not found. Available: {', '.join(available)}"

    c = portfolio["client"]
    holdings = portfolio["holdings"]
    total_current = sum(h["shares"] * h["current_price"] for h in holdings)
    total_cost = sum(h["shares"] * h["avg_cost_basis"] for h in holdings)
    overall_return = ((total_current - total_cost) / total_cost) * 100 if total_cost else 0.0

    sector_values: dict[str, float] = {}
    for h in holdings:
        value = h["shares"] * h["current_price"]
        sector_values[h["sector"]] = sector_values.get(h["sector"], 0.0) + value
    sector_allocation = {s: round((v / total_current) * 100, 1) for s, v in sector_values.items() if total_current}

    holdings_detail = []
    for h in holdings:
        current_value = h["shares"] * h["current_price"]
        gain_pct = ((h["current_price"] - h["avg_cost_basis"]) / h["avg_cost_basis"]) * 100 if h["avg_cost_basis"] else 0.0
        holdings_detail.append(
            {
                "ticker": h["ticker"],
                "company": h["company_name"],
                "shares": h["shares"],
                "avg_cost": h["avg_cost_basis"],
                "current_price": h["current_price"],
                "current_value": current_value,
                "unrealized_gain_pct": round(gain_pct, 1),
                "portfolio_weight_pct": round((current_value / total_current) * 100, 1) if total_current else 0.0,
                "sector": h["sector"],
                "ytd_return": h["ytd_return_pct"],
                "analyst_rating": h["analyst_rating"],
                "purchase_date": h["purchase_date"],
            }
        )

    result = {
        "client_id": c["client_id"],
        "name": c["name"],
        "relationship_manager": c.get("relationship_mgr"),
        "risk_profile": c["risk_profile"],
        "investment_horizon": c.get("investment_horizon"),
        "aum_inr": c["aum_inr"],
        "last_review": c.get("last_review"),
        "total_portfolio_value": round(total_current),
        "total_cost_basis": round(total_cost),
        "overall_return_pct": round(overall_return, 1),
        "sector_allocation": sector_allocation,
        "holdings": holdings_detail,
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


@tool
def market_data_search(query: str) -> str:
    """Search market data by ticker, sector, or company name."""
    results = search_market_data(query)
    if not results:
        all_tickers = [r["ticker"] for r in query_db("SELECT ticker FROM market_data")]
        return f"No data found for '{query}'. Available tickers: {', '.join(all_tickers)}"

    formatted = []
    for r in results:
        formatted.append(
            {
                "ticker": r["ticker"],
                "company": r["company_name"],
                "sector": r["sector"],
                "current_price": r["current_price"],
                "ytd_return_pct": r["ytd_return_pct"],
                "pe_ratio": r["pe_ratio"],
                "analyst_rating": r["analyst_rating"],
                "52w_range": f"{r['low_52w']} - {r['high_52w']}",
                "market_cap_cr": r.get("market_cap_cr"),
            }
        )
    return json.dumps(formatted, indent=2, ensure_ascii=False)


@tool
def calculate_metrics(expression: str) -> str:
    """Compute financial metrics and ratios from a numeric expression."""
    try:
        numbers = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+\.?\d*", expression)]
        lower = expression.lower()

        if ("return" in lower or "gain" in lower) and len(numbers) >= 2:
            current, cost = numbers[0], numbers[1]
            if cost == 0:
                return "Cost basis is zero; cannot compute return."
            ret = ((current - cost) / cost) * 100
            return f"Return: ({_format_currency(current)} - {_format_currency(cost)}) / {_format_currency(cost)} = {ret:+.2f}%"

        if any(token in lower for token in ["percentage", "allocation", "weight"]) and len(numbers) >= 2:
            part, whole = numbers[0], numbers[1]
            if whole == 0:
                return "Total value is zero; cannot compute percentage."
            return f"Percentage: {_format_currency(part)} / {_format_currency(whole)} = {(part / whole) * 100:.2f}%"

        if "compare" in lower and len(numbers) >= 2:
            a, b = numbers[0], numbers[1]
            if b == 0:
                return "Cannot compare against zero."
            return f"Comparison: {a:,.2f} vs {b:,.2f} | Diff: {a-b:+,.2f} ({((a-b)/b)*100:+.2f}%)"

        if len(numbers) == 2:
            a, b = numbers
            if b == 0:
                ratio = "infinite"
            else:
                ratio = f"{a/b:.4f}"
            return f"Values: {a:,.2f} and {b:,.2f} | Sum: {a+b:,.2f} | Diff: {a-b:+.2f} | Ratio: {ratio}"

        return f"Provide two numbers and an operation (return, percentage, compare). Got: '{expression}'"
    except Exception as exc:
        return f"Calculation error: {exc}"


@tool
def policy_retriever(query: str) -> str:
    """Retrieve relevant policy excerpts from the firm's policy documents."""
    docs = get_policy_retriever_chain().invoke(query)
    results = []
    for i, doc in enumerate(docs, start=1):
        src = os.path.basename(doc.metadata.get("source", "unknown"))
        page = doc.metadata.get("page", "?")
        results.append(f"[Policy Doc {i}: {src} | Page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(results)


def create_tavily_search_tool() -> TavilySearch:
    settings = get_settings()
    return TavilySearch(max_results=settings.tavily_max_results, topic=settings.tavily_topic)


def get_tools() -> list[Any]:
    return [
        portfolio_lookup,
        market_data_search,
        calculate_metrics,
        policy_retriever,
        create_tavily_search_tool(),
    ]
