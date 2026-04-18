import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="ForexAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.on_event("startup")
async def startup():
    print("=== SERVER STARTED ===", flush=True)

# Import routers after app is defined
from app.routers import signals, trades, analytics, auth, websocket
app.include_router(auth.router,      prefix="/api/v1/auth")
app.include_router(signals.router,   prefix="/api/v1/signals")
app.include_router(trades.router,    prefix="/api/v1/trades")
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(websocket.router, prefix="/ws")
