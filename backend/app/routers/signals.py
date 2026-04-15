"""Signals API — get latest signals, filter, trigger manual generation."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.auth import require_auth, get_user_id
from app.database import get_supabase
from app.models.schemas import SignalOut, LotSizeRequest, LotSizeResponse
from app.services.signal_service import generate_signal_for_pair, calculate_lot_size
from app.services.telegram_service import send_signal_alert

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_signals(
    pair:      Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    status:    Optional[str] = Query(None),
    limit:     int = Query(50, ge=1, le=200),
    _: dict = Depends(require_auth),
):
    """List signals with optional filters. Requires authentication."""
    db = get_supabase()
    query = db.table("signals").select("*").order("created_at", desc=True).limit(limit)

    if pair:      query = query.eq("pair", pair)
    if direction: query = query.eq("direction", direction)
    if status:    query = query.eq("status", status)

    result = query.execute()
    return result.data or []


@router.get("/latest", response_model=List[dict])
async def latest_signals(_: dict = Depends(require_auth)):
    """Get the 10 most recent active signals."""
    db = get_supabase()
    result = (
        db.table("signals")
        .select("*")
        .eq("status", "ACTIVE")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    return result.data or []


@router.get("/{signal_id}", response_model=dict)
async def get_signal(signal_id: str, _: dict = Depends(require_auth)):
    """Get a specific signal by ID."""
    db = get_supabase()
    result = db.table("signals").select("*").eq("id", signal_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Signal not found")
    return result.data


@router.post("/generate/{pair}", response_model=dict)
async def trigger_signal_generation(
    pair: str,
    timeframe: str = Query("1h"),
    _: dict = Depends(require_auth),
):
    """
    Manually trigger signal generation for a specific pair.
    Useful for testing and on-demand signals.
    """
    pair = pair.replace("-", "/").upper()
    signal = await generate_signal_for_pair(pair, timeframe)
    if not signal:
        raise HTTPException(
            status_code=422,
            detail="Could not generate a high-confidence signal for this pair right now."
        )

    # Persist to DB
    db = get_supabase()
    db.table("signals").insert(signal).execute()

    # Send Telegram alert (non-blocking, fire-and-forget)
    import asyncio
    asyncio.create_task(send_signal_alert(signal))

    return signal


@router.post("/lot-size", response_model=LotSizeResponse)
async def lot_size_calculator(
    req: LotSizeRequest,
    _: dict = Depends(require_auth),
):
    """Risk-based lot size calculator."""
    result = calculate_lot_size(
        account_balance=req.account_balance,
        risk_percent=req.risk_percent,
        stop_loss_pips=req.stop_loss_pips,
        pair=req.pair,
    )
    return result
