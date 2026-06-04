from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .config import get_settings


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    return connection


def query_db(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
    return rows


def get_client_portfolio(client_id: str) -> dict[str, Any] | None:
    client_id = client_id.upper().strip()
    client = query_db("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    if not client:
        return None

    holdings = query_db(
        """
        SELECT h.ticker, h.company_name, h.shares, h.avg_cost_basis, h.current_price,
               h.sector, h.purchase_date,
               m.ytd_return_pct, m.pe_ratio, m.analyst_rating, m.high_52w, m.low_52w, m.market_cap_cr
        FROM holdings h
        LEFT JOIN market_data m ON h.ticker = m.ticker
        WHERE h.client_id = ?
        ORDER BY (h.shares * h.current_price) DESC
        """,
        (client_id,),
    )

    return {"client": client[0], "holdings": holdings}


def search_market_data(query: str) -> list[dict[str, Any]]:
    q = query.upper().strip()
    results = query_db("SELECT * FROM market_data WHERE ticker = ?", (q,))
    if results:
        return results

    like_query = f"%{q}%"
    results = query_db(
        "SELECT * FROM market_data WHERE UPPER(sector) LIKE ? OR UPPER(company_name) LIKE ? OR ticker LIKE ?",
        (like_query, like_query, like_query),
    )
    return results
