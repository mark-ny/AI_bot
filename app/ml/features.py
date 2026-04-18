"""
Feature engineering for the ML model.
Uses the `ta` library for reliable technical indicator calculation.
All features are normalised to be stationary (returns, ratios, z-scores).
"""
import numpy as np
import pandas as pd
import ta

# Feature columns consumed by the XGBoost model (must match training order)
FEATURE_COLUMNS = [
    "rsi_14",
    "rsi_change",
    "ema_9_20_cross",
    "ema_20_50_cross",
    "macd_hist",
    "macd_hist_change",
    "bb_position",
    "bb_width",
    "atr_norm",
    "price_change_1",
    "price_change_3",
    "price_change_6",
    "volume_ratio",
    "high_low_range",
    "close_vs_ema20",
    "close_vs_ema50",
    "stoch_k",
    "stoch_d",
    "williams_r",
    "adx",
]


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all features from an OHLCV DataFrame.
    Returns a DataFrame with FEATURE_COLUMNS ready for ML inference.
    Input df must have columns: open, high, low, close, volume (float)
    Requires at least 60 rows.
    """
    if len(df) < 60:
        return pd.DataFrame()

    out = pd.DataFrame(index=df.index)

    close = df["close"]
    high  = df["high"]
    low   = df["low"]
    vol   = df["volume"].replace(0, np.nan).ffill().fillna(1)

    # ── RSI ──────────────────────────────────────────────────────
    rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    out["rsi_14"]     = rsi / 100.0          # normalised 0–1
    out["rsi_change"] = rsi.diff(3) / 100.0

    # ── EMA crossovers ───────────────────────────────────────────
    ema9  = ta.trend.EMAIndicator(close=close, window=9).ema_indicator()
    ema20 = ta.trend.EMAIndicator(close=close, window=20).ema_indicator()
    ema50 = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()

    out["ema_9_20_cross"]  = (ema9 - ema20) / close
    out["ema_20_50_cross"] = (ema20 - ema50) / close
    out["close_vs_ema20"]  = (close - ema20) / close
    out["close_vs_ema50"]  = (close - ema50) / close

    # ── MACD ─────────────────────────────────────────────────────
    macd_obj  = ta.trend.MACD(close=close, window_fast=12, window_slow=26, window_sign=9)
    macd_hist = macd_obj.macd_diff()
    out["macd_hist"]        = macd_hist / close
    out["macd_hist_change"] = macd_hist.diff(2) / close

    # ── Bollinger Bands ───────────────────────────────────────────
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband()
    bb_lower = bb.bollinger_lband()
    bb_width = bb_upper - bb_lower
    out["bb_position"] = (close - bb_lower) / bb_width.replace(0, np.nan)
    out["bb_width"]    = bb_width / close

    # ── ATR (volatility) ─────────────────────────────────────────
    atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    out["atr_norm"] = atr / close

    # ── Price momentum ────────────────────────────────────────────
    out["price_change_1"] = close.pct_change(1)
    out["price_change_3"] = close.pct_change(3)
    out["price_change_6"] = close.pct_change(6)

    # ── Volume ratio ──────────────────────────────────────────────
    vol_ma = vol.rolling(20).mean()
    out["volume_ratio"] = (vol / vol_ma.replace(0, np.nan)).fillna(1.0)

    # ── Price range ───────────────────────────────────────────────
    out["high_low_range"] = (high - low) / close

    # ── Stochastic oscillator ─────────────────────────────────────
    stoch = ta.momentum.StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    out["stoch_k"] = stoch.stoch() / 100.0
    out["stoch_d"] = stoch.stoch_signal() / 100.0

    # ── Williams %R ───────────────────────────────────────────────
    out["williams_r"] = ta.momentum.WilliamsRIndicator(high=high, low=low, close=close, lbp=14).williams_r() / -100.0

    # ── ADX (trend strength) ──────────────────────────────────────
    out["adx"] = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14).adx() / 100.0

    # Drop NaN rows introduced by rolling windows
    out = out[FEATURE_COLUMNS].dropna()
    return out


def label_direction(df: pd.DataFrame, forward_periods: int = 3, threshold: float = 0.0003) -> pd.Series:
    """
    Create training labels: 1 = price goes UP > threshold, 0 = DOWN or flat.
    Uses future returns so this is only valid for historical training data.
    """
    future_return = df["close"].shift(-forward_periods) / df["close"] - 1
    return (future_return > threshold).astype(int)
