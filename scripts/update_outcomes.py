#!/usr/bin/env python3
"""
Signal outcome updater.
Checks all ACTIVE signals and marks them TP_HIT or SL_HIT
based on whether the current price has crossed TP or SL.

Run as a cron job or call from the scheduler.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))


async def update_signal_outcomes():
    from app.database import get_supabase
    from app.services.data_service import get_ohlcv
    from datetime import datetime, timezone

    db = get_supabase()
    result = db.table("signals").select("*").eq("status", "ACTIVE").execute()
    active = result.data or []

    if not active:
        print("[updater] No active signals to check")
        return

    print(f"[updater] Checking {len(active)} active signals...")
    updated = 0

    for sig in active:
        try:
            df = await get_ohlcv(sig["pair"], interval="1h", bars=10)
            current = float(df["close"].iloc[-1])
            high    = float(df["high"].iloc[-1])
            low     = float(df["low"].iloc[-1])

            tp = float(sig["take_profit"])
            sl = float(sig["stop_loss"])
            entry = float(sig["entry_price"])
            is_buy = sig["direction"] == "BUY"

            new_status = None
            pnl_pips = None

            if is_buy:
                if high >= tp:
                    new_status = "TP_HIT"
                    pnl_pips   = round((tp - entry) * 10_000, 1)
                elif low <= sl:
                    new_status = "SL_HIT"
                    pnl_pips   = round((sl - entry) * 10_000, 1)
            else:
                if low <= tp:
                    new_status = "TP_HIT"
                    pnl_pips   = round((entry - tp) * 10_000, 1)
                elif high >= sl:
                    new_status = "SL_HIT"
                    pnl_pips   = round((entry - sl) * 10_000, 1)

            if new_status:
                db.table("signals").update({
                    "status":    new_status,
                    "pnl_pips":  pnl_pips,
                    "closed_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", sig["id"]).execute()
                print(f"[updater] {sig['pair']} {sig['direction']} → {new_status} ({pnl_pips:+.1f} pips)")
                updated += 1

        except Exception as exc:
            print(f"[updater] Error checking {sig['pair']}: {exc}")

    print(f"[updater] Updated {updated} signals")


if __name__ == "__main__":
    asyncio.run(update_signal_outcomes())
