"""Analytics API — win rate, drawdown, model metrics, performance stats."""
from fastapi import APIRouter, Depends
from app.auth import require_auth, get_user_id
from app.database import get_supabase

router = APIRouter()


@router.get("/performance")
async def get_performance(_: dict = Depends(require_auth)):
    """
    Aggregate performance statistics for all closed signals.
    Returns win rate, pip totals, avg confidence, drawdown.
    """
    db = get_supabase()
    result = db.table("signals").select("*").neq("status", "ACTIVE").execute()
    signals = result.data or []

    if not signals:
        return {
            "total_signals": 0, "win_rate": 0.0, "total_pips": 0.0,
            "avg_confidence": 0.0, "best_pair": None,
            "current_drawdown": 0.0, "profit_factor": 0.0,
        }

    wins        = [s for s in signals if s["status"] == "TP_HIT"]
    losses      = [s for s in signals if s["status"] == "SL_HIT"]
    win_pips    = sum(s.get("pnl_pips", 0) or 0 for s in wins)
    loss_pips   = abs(sum(s.get("pnl_pips", 0) or 0 for s in losses))
    total_pips  = win_pips - loss_pips
    win_rate    = len(wins) / len(signals) if signals else 0.0

    # Best performing pair
    pair_wins: dict[str, int] = {}
    for s in wins:
        pair_wins[s["pair"]] = pair_wins.get(s["pair"], 0) + 1
    best_pair = max(pair_wins, key=pair_wins.get) if pair_wins else None

    # Profit factor
    profit_factor = (win_pips / loss_pips) if loss_pips > 0 else float(win_pips > 0)

    # Simplified max drawdown (equity curve simulation)
    equity = 0.0
    peak   = 0.0
    max_dd = 0.0
    for s in sorted(signals, key=lambda x: x["created_at"]):
        equity += (s.get("pnl_pips", 0) or 0)
        peak    = max(peak, equity)
        dd      = peak - equity
        max_dd  = max(max_dd, dd)

    return {
        "total_signals":    len(signals),
        "win_rate":         round(win_rate, 4),
        "total_pips":       round(total_pips, 1),
        "avg_confidence":   round(
            sum(s.get("confidence", 0) for s in signals) / len(signals), 4
        ),
        "best_pair":        best_pair,
        "current_drawdown": round(max_dd, 1),
        "profit_factor":    round(profit_factor, 2),
    }


@router.get("/model-metrics")
async def get_model_metrics(_: dict = Depends(require_auth)):
    """Latest ML model training metrics."""
    db = get_supabase()
    result = (
        db.table("model_metrics")
        .select("*")
        .order("trained_at", desc=True)
        .limit(10)
        .execute()
    )
    return result.data or []


@router.get("/user-stats")
async def get_user_stats(user_id: str = Depends(get_user_id)):
    """Per-user trading stats from their recorded trades."""
    db = get_supabase()
    trades = (
        db.table("trades")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "CLOSED")
        .execute()
    ).data or []

    if not trades:
        return {"total_trades": 0, "total_pnl_usd": 0.0, "win_rate": 0.0}

    wins         = [t for t in trades if (t.get("pnl_usd") or 0) > 0]
    total_pnl    = sum(t.get("pnl_usd", 0) or 0 for t in trades)
    win_rate     = len(wins) / len(trades) if trades else 0.0

    return {
        "total_trades": len(trades),
        "total_pnl_usd": round(total_pnl, 2),
        "win_rate":      round(win_rate, 4),
    }
