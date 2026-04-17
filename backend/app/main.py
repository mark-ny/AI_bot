"""
Forex Signal Platform — FastAPI Backend
Entry point: uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle — all steps are non-fatal."""

    # 1. Validate critical env vars and log clearly if missing
    from app.config import get_settings
    try:
        settings = get_settings()
        logger.info(f"[startup] Environment: {settings.environment}")
        logger.info(f"[startup] Supabase URL configured: {bool(settings.supabase_url)}")
        logger.info(f"[startup] Twelve Data key set: {bool(settings.twelve_data_api_key)}")
    except Exception as exc:
        logger.error(
            f"[startup] CONFIGURATION ERROR: {exc}\n"
            "Set SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_JWT_SECRET "
            "in Render → Environment tab, then redeploy."
        )
        # Still yield so the health endpoint responds — avoids Render boot loop
        yield
        return

    # 2. Load ML model (non-fatal — will train on first scheduler run)
    try:
        from app.ml.model_manager import ModelManager
        manager = ModelManager.get_instance()
        await manager.initialize()
    except Exception as exc:
        logger.error(f"[startup] ML model init failed (non-fatal): {exc}")

    # 3. Start background scheduler
    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
    except Exception as exc:
        logger.error(f"[startup] Scheduler start failed (non-fatal): {exc}")

    logger.info("[startup] Server ready ✓")
    yield

    # Graceful shutdown
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="Forex Signal Platform API",
    version="1.0.0",
    description="AI-powered forex signal generation with XGBoost ML",
    lifespan=lifespan,
)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.routers import signals, trades, analytics, auth, websocket
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["auth"])
app.include_router(signals.router,   prefix="/api/v1/signals",   tags=["signals"])
app.include_router(trades.router,    prefix="/api/v1/trades",    tags=["trades"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(websocket.router, prefix="/ws",               tags=["websocket"])


@app.get("/health")
async def health_check():
    """Health endpoint — always responds 200 so Render doesn't kill the process."""
    return {"status": "ok", "version": "1.0.0"}
