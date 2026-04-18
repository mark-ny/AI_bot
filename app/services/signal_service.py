"""
Signal generation service.
Uses ML predictions + ATR-based SL/TP to produce trade signals.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from app.services.data_service import get_ohlcv, SUPPORTED_PAIRS
from app.ml.model_manager import ModelManager
from app.ml.features import compute_features
from app.database import get_supabase


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    """Average True Range — used for dynamic SL/TP sizing."""
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


async def generate_signal_for_pair(pair: str, timeframe: str = "1h") -> Optional[dict]:
    """
    Full pipeline: fetch data → engineer features → predict → build signal.
    Returns a signal dict ready to insert into Supabase, or None on failure.
    """
    # 1. Fetch OHLCV
    df = await get_ohlcv(pair, interval=timeframe, bars=300)

    # 2. Compute technical features
    features_df = compute_features(df)
    if features_df.empty:
        return None

    last_row = features_df.iloc[[-1]]

    # 3. Run ML prediction
    manager = ModelManager.get_instance()
    prediction = manager.predict(last_row)
    if prediction is None:
        return None

    direction   = "BUY" if prediction["direction"] == 1 else "SELL"
    confidence  = float(prediction["confidence"])

    # Only emit signals above confidence threshold
    if confidence < 0.58:
        return None

    # 4. Compute entry, SL, TP using ATR
    current_price = float(df["close"].iloc[-1])
    atr = _atr(df)

    sl_multiplier = 1.5
    tp_multiplier = 2.5  # default 1.67 R:R

    if direction == "BUY":
        entry      = current_price
        stop_loss  = round(entry - atr * sl_multiplier, 5)
        take_profit= round(entry + atr * tp_multiplier, 5)
    else:
        entry      = current_price
        stop_loss  = round(entry + atr * sl_multiplier, 5)
        take_profit= round(entry - atr * tp_multiplier, 5)

    risk_pips   = abs(entry - stop_loss) * 10_000
    reward_pips = abs(take_profit - entry) * 10_000
    risk_reward = round(reward_pips / risk_pips, 2) if risk_pips else 0

    signal = {
        "id":           str(uuid.uuid4()),
        "pair":         pair,
        "direction":    direction,
        "entry_price":  round(entry, 5),
        "stop_loss":    stop_loss,
        "take_profit":  take_profit,
        "confidence":   round(confidence, 4),
        "risk_reward":  risk_reward,
        "timeframe":    timeframe,
        "status":       "ACTIVE",
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    return signal


async def generate_all_signals() -> list[dict]:
    """
    Generate signals for all supported pairs.
    Called by scheduler every hour.
    """
    signals = []
    for pair in SUPPORTED_PAIRS:
        try:
            sig = await generate_signal_for_pair(pair)
            if sig:
                signals.append(sig)
        except Exception as exc:
            # Log but don't crash the whole batch
            print(f"[signal] Error generating for {pair}: {exc}")

    if signals:
        # Batch insert into Supabase
        db = get_supabase()
        db.table("signals").insert(signals).execute()
        print(f"[signal] Inserted {len(signals)} new signals")

    return signals


def calculate_lot_size(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    pair: str,
) -> dict:
    """
    Position sizing: risk-based lot size calculation.
    Standard: 1 lot = 100,000 units; 1 pip ≈ $10 for USD pairs.
    """
    # Approximate pip value for major pairs (USD-denominated account)
    pip_values = {
        "EUR/USD": 10.0, "GBP/USD": 10.0, "AUD/USD": 10.0,
        "NZD/USD": 10.0, "USD/CAD": 7.5,  "USD/CHF": 10.8,
        "USD/JPY": 9.1,  "EUR/GBP": 12.5, "EUR/JPY": 9.1,
        "GBP/JPY": 9.1,
    }
    pip_value_per_lot = pip_values.get(pair, 10.0)

    risk_amount    = account_balance * (risk_percent / 100)
    lot_size       = round(risk_amount / (stop_loss_pips * pip_value_per_lot), 2)
    max_loss_usd   = round(lot_size * stop_loss_pips * pip_value_per_lot, 2)

    return {
        "lot_size":       max(0.01, min(lot_size, 100.0)),
        "risk_amount_usd": round(risk_amount, 2),
        "pip_value":       pip_value_per_lot,
        "max_loss_usd":    max_loss_usd,
    }
