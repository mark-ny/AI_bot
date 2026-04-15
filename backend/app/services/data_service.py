"""
Forex data fetcher.
Primary:  Twelve Data  (free tier: 800 requests/day)
Fallback: Alpha Vantage (free tier: 25 requests/day)
"""
import httpx
import pandas as pd
from typing import Optional
from app.config import get_settings

TWELVE_BASE = "https://api.twelvedata.com"
AV_BASE     = "https://www.alphavantage.co/query"

# Supported pairs (major + minor forex)
SUPPORTED_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "USD/CAD", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY",
]


async def fetch_ohlcv_twelve(
    pair: str,
    interval: str = "1h",
    outputsize: int = 200,
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV from Twelve Data.
    interval: 1min | 5min | 15min | 30min | 1h | 4h | 1day
    """
    settings = get_settings()
    if not settings.twelve_data_api_key:
        return None

    symbol = pair.replace("/", "")
    url = f"{TWELVE_BASE}/time_series"
    params = {
        "symbol":     symbol,
        "interval":   interval,
        "outputsize": outputsize,
        "apikey":     settings.twelve_data_api_key,
        "format":     "JSON",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "values" not in data:
        return None

    df = pd.DataFrame(data["values"])
    df = df.rename(columns={
        "datetime": "timestamp",
        "open": "open", "high": "high",
        "low": "low",  "close": "close",
        "volume": "volume",
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df.get("volume", pd.Series([0.0] * len(df))).astype(float)
    return df


async def fetch_ohlcv_alpha(
    pair: str,
    interval: str = "60min",
) -> Optional[pd.DataFrame]:
    """
    Fallback: Alpha Vantage FX_INTRADAY endpoint.
    """
    settings = get_settings()
    if not settings.alpha_vantage_api_key:
        return None

    from_sym, to_sym = pair.split("/")
    params = {
        "function":    "FX_INTRADAY",
        "from_symbol": from_sym,
        "to_symbol":   to_sym,
        "interval":    interval,
        "outputsize":  "full",
        "apikey":      settings.alpha_vantage_api_key,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(AV_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    key = f"Time Series FX ({interval})"
    if key not in data:
        return None

    rows = []
    for ts, vals in data[key].items():
        rows.append({
            "timestamp": pd.to_datetime(ts),
            "open":  float(vals["1. open"]),
            "high":  float(vals["2. high"]),
            "low":   float(vals["3. low"]),
            "close": float(vals["4. close"]),
            "volume": 0.0,
        })

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df


async def get_ohlcv(
    pair: str,
    interval: str = "1h",
    bars: int = 200,
) -> pd.DataFrame:
    """
    Primary entry point — tries Twelve Data first, falls back to Alpha Vantage.
    Raises RuntimeError if both fail.
    """
    df = await fetch_ohlcv_twelve(pair, interval, bars)
    if df is not None and len(df) >= 50:
        return df

    # Map interval for Alpha Vantage
    av_interval_map = {"1h": "60min", "4h": "60min", "15m": "15min", "1d": "Daily"}
    av_interval = av_interval_map.get(interval, "60min")
    df = await fetch_ohlcv_alpha(pair, av_interval)

    if df is None or len(df) < 50:
        raise RuntimeError(
            f"Could not fetch OHLCV data for {pair}. "
            "Check API keys in .env (TWELVE_DATA_API_KEY or ALPHA_VANTAGE_API_KEY)."
        )
    return df
