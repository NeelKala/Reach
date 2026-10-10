"""Read-only market quote integration for Zerodha Kite Connect."""

import asyncio
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import settings


# NSE trading symbols supported by Kite Connect.
WATCHLIST = [
    {"symbol": "RELIANCE", "name": "Reliance Industries"},
    {"symbol": "TCS", "name": "Tata Consultancy Services"},
    {"symbol": "INFY", "name": "Infosys"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank"},
    {"symbol": "LT", "name": "Larsen & Toubro"},
]


def _fetch_quotes_sync() -> dict:
    api_key = getattr(settings, "kite_api_key", "")
    access_token = getattr(settings, "kite_access_token", "")
    if not api_key or not access_token:
        raise RuntimeError(
            "Zerodha Kite Connect is not configured. Set KITE_API_KEY and KITE_ACCESS_TOKEN."
        )

    instruments = [f"NSE:{stock['symbol']}" for stock in WATCHLIST]
    query = urlencode([("i", instrument) for instrument in instruments])
    request = Request(
        f"https://api.kite.trade/quote/ohlc?{query}",
        headers={
            "Authorization": f"token {api_key}:{access_token}",
            "X-Kite-Version": "3",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not return response headers or credentials to the frontend.
        if exc.code in (401, 403):
            raise RuntimeError(
                "Zerodha authentication failed. Check the API key and daily access token."
            ) from exc
        if exc.code == 429:
            raise RuntimeError("Zerodha rate limit reached. Retry shortly.") from exc
        raise RuntimeError(f"Zerodha quote request failed (HTTP {exc.code}).") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not retrieve quotes from Zerodha.") from exc

    if payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
        raise RuntimeError("Zerodha returned an unexpected quote response.")

    quote_data = payload["data"]
    items = []
    for stock in WATCHLIST:
        key = f"NSE:{stock['symbol']}"
        quote = quote_data.get(key)
        if not isinstance(quote, dict) or quote.get("last_price") is None:
            continue

        last_price = float(quote["last_price"])
        ohlc = quote.get("ohlc") or {}
        previous_close = float(ohlc["close"]) if ohlc.get("close") is not None else None
        change = last_price - previous_close if previous_close and previous_close > 0 else None
        change_pct = (change / previous_close * 100) if change is not None else None

        items.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "exchange": "NSE",
            "currency": "INR",
            "last_price": last_price,
            "previous_close": previous_close,
            "change": change,
            "change_pct": change_pct,
        })

    if not items:
        raise RuntimeError("Zerodha returned no usable quotes for the configured watchlist.")

    return {
        "source": "Zerodha Kite Connect",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }


async def market_quotes() -> dict:
    """Run blocking stdlib HTTP work outside the event loop."""
    return await asyncio.to_thread(_fetch_quotes_sync)
