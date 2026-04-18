"""Trades API — record user trades, close them, track P&L."""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import uuid

from app.auth import require_auth, get_user_id
from app.database import get_supabase
from app.models.schemas import TradeCreate, TradeOut

router = APIRouter()


@router.get("/", response_model=list)
async def list_trades(
    user_id: str = Depends(get_user_id),
):
    """Get all trades for the authenticated user."""
    db = get_supabase()
    result = (
        db.table("trades")
        .select("*, signals(*)")
        .eq("user_id", user_id)
        .order("opened_at", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/", response_model=dict)
async def open_trade(
    body: TradeCreate,
    user_id: str = Depends(get_user_id),
):
    """Record a new trade based on a signal."""
    db = get_supabase()

    # Verify signal exists
    sig_result = db.table("signals").select("id").eq("id", body.signal_id).execute()
    if not sig_result.data:
        raise HTTPException(status_code=404, detail="Signal not found")

    trade = {
        "id":         str(uuid.uuid4()),
        "user_id":    user_id,
        "signal_id":  body.signal_id,
        "lot_size":   body.lot_size,
        "notes":      body.notes,
        "status":     "OPEN",
        "opened_at":  datetime.now(timezone.utc).isoformat(),
    }
    result = db.table("trades").insert(trade).execute()
    return result.data[0]


@router.patch("/{trade_id}/close", response_model=dict)
async def close_trade(
    trade_id: str,
    pnl_usd: float,
    user_id: str = Depends(get_user_id),
):
    """Close a trade and record P&L."""
    db = get_supabase()

    # Ensure trade belongs to the user
    existing = (
        db.table("trades")
        .select("id, user_id, status")
        .eq("id", trade_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Trade not found")
    if existing.data["status"] == "CLOSED":
        raise HTTPException(status_code=400, detail="Trade already closed")

    result = (
        db.table("trades")
        .update({
            "status":    "CLOSED",
            "pnl_usd":   pnl_usd,
            "closed_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", trade_id)
        .execute()
    )
    return result.data[0]


@router.delete("/{trade_id}", status_code=204)
async def delete_trade(trade_id: str, user_id: str = Depends(get_user_id)):
    """Delete an open trade (cancel before execution)."""
    db = get_supabase()
    db.table("trades").delete().eq("id", trade_id).eq("user_id", user_id).execute()
