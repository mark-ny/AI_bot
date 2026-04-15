"""
Telegram alert service — sends signal notifications to a channel.
Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable.
"""
import httpx
from app.config import get_settings


async def send_signal_alert(signal: dict) -> bool:
    """
    Send a formatted signal alert to the Telegram channel.
    Returns True on success, False if disabled or on error.
    """
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False  # Silently skip if not configured

    direction_emoji = "🟢" if signal["direction"] == "BUY" else "🔴"
    confidence_pct  = round(signal["confidence"] * 100, 1)

    message = (
        f"{direction_emoji} *{signal['direction']} {signal['pair']}*\n"
        f"⏱ Timeframe: `{signal['timeframe']}`\n"
        f"📍 Entry:  `{signal['entry_price']}`\n"
        f"🛑 SL:     `{signal['stop_loss']}`\n"
        f"🎯 TP:     `{signal['take_profit']}`\n"
        f"📊 R:R     `1:{signal['risk_reward']}`\n"
        f"🧠 Confidence: `{confidence_pct}%`"
    )

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id":    settings.telegram_chat_id,
        "text":       message,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as exc:
        print(f"[telegram] Alert failed: {exc}")
        return False
