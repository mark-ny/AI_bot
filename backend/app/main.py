"""
Forex Signal Platform — FastAPI Backend
Entry point: uvicorn app.main:app --reload
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import signals, trades, analytics, auth, websocket
from app.services.scheduler import start_scheduler, stop_scheduler
from app.ml.model_manager import ModelManager

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Initialize ML model on startup
    manager = ModelManager.get_instance()
    await manager.initialize()

    # Start background scheduler (daily retrain + signal generation)
    start_scheduler()

    yield

    # Graceful shutdown
    stop_scheduler()


app = FastAPI(
    title="Forex Signal Platform API",
    version="1.0.0",
    description="AI-powered forex signal generation with XGBoost ML",
    lifespan=lifespan,
)

# CORS — allow frontend origins
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["auth"])
app.include_router(signals.router,   prefix="/api/v1/signals",   tags=["signals"])
app.include_router(trades.router,    prefix="/api/v1/trades",    tags=["trades"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(websocket.router, prefix="/ws",               tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
