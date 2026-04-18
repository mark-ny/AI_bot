"""
Forex Signal Platform — FastAPI Backend
Entry point: uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
import sys
import os

# ── Path fix (must be first, before any other app imports) ────
# Ensure the backend directory is on sys.path so all `app.*`
# imports resolve correctly regardless of Render's working directory.
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
# ─────────────────────────────────────────────────────────────

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle — all steps are non-fatal."""

    logger.info(f"[startup] Backend dir on sys.path: {_backend_dir}")
    logger.info(f"[startup] Python version: {sys.version}")

    from app.config import get_settings
    try:
        settings = get_settings()
        logger.info(f"[startup] Environment: {settings.environment}")
        logger.info(f"[startup] Supabase configured: {bool(settings.supabase_url)}")
        logger.info(f"[startup] Twelve Data key set: {bool(settings.twelve_data_api_key)}")
    except Exception as exc:
        logger.error(
            f"[startup] CONFIG ERROR: {exc}\n"
            "Set SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_JWT_SECRET "
            "in Render → Environment tab, then redeploy."
        )
        yield
        return

    try:
        from app.ml.model_manager import ModelManager
        await ModelManager.get_instance().initialize()
    except Exception as exc:
        logger.error(f"[startup] ML init failed (non-fatal): {exc}")

    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
    except Exception as exc:
        logger.error(f"[startup] Scheduler failed (non-fatal): {exc}")

    logger.info("[startup] Server ready ✓")
    yield

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

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import signals, trades, analytics, auth, websocket
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["auth"])
app.include_router(signals.router,   prefix="/api/v1/signals",   tags=["signals"])
app.include_router(trades.router,    prefix="/api/v1/trades",    tags=["trades"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(websocket.router, prefix="/ws",               tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
