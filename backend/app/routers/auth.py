"""
Auth router — lightweight proxy for Supabase Auth operations.
Supabase handles the actual JWT issuing; this router manages
user profile creation on first login and subscription lookup.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.auth import require_auth, get_user_id
from app.database import get_supabase
import uuid
from datetime import datetime, timezone

router = APIRouter()


@router.get("/me")
async def get_profile(user_id: str = Depends(get_user_id)):
    """Return user profile + subscription tier."""
    db = get_supabase()

    # Fetch user row
    user_result = (
        db.table("users").select("*").eq("id", user_id).execute()
    )
    user = user_result.data[0] if user_result.data else None

    if not user:
        # First login — create profile row
        user = {
            "id":         user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db.table("users").insert(user).execute()

        # Grant free subscription
        db.table("subscriptions").insert({
            "id":      str(uuid.uuid4()),
            "user_id": user_id,
            "plan":    "free",
            "status":  "active",
        }).execute()

    # Fetch subscription
    sub_result = (
        db.table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    subscription = sub_result.data[0] if sub_result.data else {"plan": "free", "status": "active"}

    return {"user": user, "subscription": subscription}


@router.get("/subscription")
async def get_subscription(user_id: str = Depends(get_user_id)):
    """Return the user's active subscription."""
    db = get_supabase()
    result = (
        db.table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return result.data[0]
