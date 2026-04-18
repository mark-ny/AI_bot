"""Pydantic schemas for all API request/response models."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Signal models ──────────────────────────────────────────────
class SignalOut(BaseModel):
    id: str
    pair: str
    direction: str          # "BUY" | "SELL"
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float       # 0.0 – 1.0
    risk_reward: float
    timeframe: str
    status: str             # "ACTIVE" | "TP_HIT" | "SL_HIT" | "EXPIRED"
    created_at: datetime
    closed_at: Optional[datetime] = None
    pnl_pips: Optional[float] = None

    class Config:
        from_attributes = True


class SignalFilter(BaseModel):
    pair: Optional[str] = None
    direction: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)


# ── Trade models ───────────────────────────────────────────────
class TradeCreate(BaseModel):
    signal_id: str
    lot_size: float = Field(gt=0, le=100)
    notes: Optional[str] = None


class TradeOut(BaseModel):
    id: str
    signal_id: str
    user_id: str
    lot_size: float
    opened_at: datetime
    closed_at: Optional[datetime] = None
    pnl_usd: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


# ── Analytics models ───────────────────────────────────────────
class PerformanceStats(BaseModel):
    total_signals: int
    win_rate: float
    total_pips: float
    avg_confidence: float
    best_pair: Optional[str] = None
    current_drawdown: float
    profit_factor: float


class ModelMetricOut(BaseModel):
    id: str
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    trained_at: datetime

    class Config:
        from_attributes = True


# ── Subscription models ────────────────────────────────────────
class SubscriptionOut(BaseModel):
    id: str
    user_id: str
    plan: str               # "free" | "pro" | "premium"
    status: str             # "active" | "cancelled" | "expired"
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Lot size calculator ────────────────────────────────────────
class LotSizeRequest(BaseModel):
    account_balance: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=100, default=1.0)
    stop_loss_pips: float = Field(gt=0)
    pair: str


class LotSizeResponse(BaseModel):
    lot_size: float
    risk_amount_usd: float
    pip_value: float
    max_loss_usd: float
