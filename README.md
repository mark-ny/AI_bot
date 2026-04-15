# ForexAI — AI-Powered Forex Signal Platform

A production-ready, self-improving forex signal platform built entirely on free-tier services.

## Features

- **AI Signal Generation** — XGBoost ML model predicts BUY/SELL direction with confidence score
- **20 Technical Indicators** — RSI, EMA crossovers, MACD, Bollinger Bands, ATR, Stochastic, ADX, Williams %R
- **Self-Learning** — Daily retraining on fresh market data; metrics stored in Supabase
- **Real-Time Updates** — Supabase Realtime pushes new signals to all connected browsers instantly
- **WebSocket Alerts** — Backend broadcasts via WebSocket on signal generation
- **Telegram Alerts** — Optional bot notifications to your channel
- **Risk Calculator** — Position sizing based on account balance and risk percentage
- **Trade Journal** — Record and track your trades with P&L
- **Performance Analytics** — Win rate, drawdown, profit factor, model health charts
- **Authentication** — Supabase Auth with email/password and Google OAuth
- **Subscription Tiers** — Free/Pro/Premium with PayPal integration
- **Dark Mode UI** — Professional trading terminal aesthetic

## Tech Stack

| Layer         | Technology                    | Host        |
|---------------|-------------------------------|-------------|
| Frontend      | Next.js 14, Tailwind CSS      | Vercel      |
| Backend API   | Python 3.11, FastAPI          | Render      |
| Database      | PostgreSQL via Supabase       | Supabase    |
| Auth          | Supabase Auth (JWT)           | Supabase    |
| ML Engine     | XGBoost, scikit-learn, pandas | Render      |
| Realtime      | Supabase Realtime             | Supabase    |
| Data Source   | Twelve Data, Alpha Vantage    | External    |

## Project Structure

```
forex-platform/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # App entry point, lifespan hooks
│   │   ├── config.py           # Pydantic settings from .env
│   │   ├── auth.py             # JWT authentication middleware
│   │   ├── database.py         # Supabase client singleton
│   │   ├── ml/
│   │   │   ├── features.py     # Technical indicator computation (20 features)
│   │   │   ├── model_manager.py# Singleton model loader/predictor
│   │   │   └── trainer.py      # XGBoost training + walk-forward CV
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── signals.py      # Signal generation endpoints
│   │   │   ├── trades.py       # Trade recording endpoints
│   │   │   ├── analytics.py    # Performance stats endpoints
│   │   │   ├── auth.py         # User profile endpoints
│   │   │   └── websocket.py    # Real-time WebSocket endpoint
│   │   └── services/
│   │       ├── data_service.py # Twelve Data + Alpha Vantage fetcher
│   │       ├── signal_service.py# ATR-based SL/TP + signal builder
│   │       ├── scheduler.py    # APScheduler: hourly signals + daily retrain
│   │       └── telegram_service.py # Alert notifications
│   ├── requirements.txt
│   ├── render.yaml
│   └── .env.example
│
├── frontend/                   # Next.js 14 frontend
│   ├── app/
│   │   ├── layout.tsx          # Root layout with dark mode + providers
│   │   ├── page.tsx            # Root redirect (auth or dashboard)
│   │   ├── globals.css         # Tailwind + custom classes
│   │   ├── dashboard/page.tsx  # Main dashboard with live signals
│   │   ├── signals/page.tsx    # Signals browser with filters
│   │   ├── history/page.tsx    # Trade history table
│   │   ├── analytics/page.tsx  # Performance + model metric charts
│   │   ├── auth/page.tsx       # Login/signup with Supabase Auth UI
│   │   └── subscribe/page.tsx  # Pricing and PayPal checkout
│   ├── components/
│   │   └── ui/
│   │       ├── AuthProvider.tsx # Supabase session context
│   │       ├── Sidebar.tsx      # Navigation sidebar
│   │       ├── SignalCard.tsx   # Signal display card
│   │       └── TradeModal.tsx   # Trade entry with lot calculator
│   ├── lib/
│   │   ├── api.ts              # Typed API client (auto-injects JWT)
│   │   ├── store.ts            # Zustand global state
│   │   └── supabase.ts         # Supabase browser client
│   ├── package.json
│   └── vercel.json
│
├── supabase/
│   └── schema.sql              # Complete DB schema + RLS policies
│
├── scripts/
│   ├── train_model.py          # Manual model training trigger
│   └── update_outcomes.py      # Mark signals TP_HIT / SL_HIT
│
├── DEPLOYMENT.md               # Step-by-step deployment guide
└── README.md
```

## API Endpoints

```
GET  /health                        Public health check

POST /api/v1/auth/me                Get/create user profile
GET  /api/v1/auth/subscription      User subscription status

GET  /api/v1/signals/               List signals (filters: pair, direction, status)
GET  /api/v1/signals/latest         Latest 10 active signals
GET  /api/v1/signals/{id}           Single signal
POST /api/v1/signals/generate/{pair} Generate signal on demand
POST /api/v1/signals/lot-size       Risk-based position size calculator

GET  /api/v1/trades/                User's trade history
POST /api/v1/trades/                Record a new trade
PATCH /api/v1/trades/{id}/close     Close trade with P&L
DELETE /api/v1/trades/{id}          Cancel trade

GET  /api/v1/analytics/performance  Aggregate signal stats
GET  /api/v1/analytics/model-metrics ML model training history
GET  /api/v1/analytics/user-stats   Per-user trade statistics

WS   /ws/signals                    Real-time signal WebSocket
```

## ML Model Details

**Algorithm:** XGBoost Classifier  
**Validation:** Time-Series Walk-Forward Cross-Validation (5 splits)  
**Training:** All 10 major forex pairs × 1h and 4h timeframes × 500 bars each  
**Retrain:** Daily at 02:00 UTC automatically  
**Threshold:** Only signals with ≥58% confidence are emitted  

**Features (20 total):**
- `rsi_14`, `rsi_change` — RSI momentum
- `ema_9_20_cross`, `ema_20_50_cross` — Trend crossovers
- `macd_hist`, `macd_hist_change` — MACD momentum
- `bb_position`, `bb_width` — Bollinger Band position
- `atr_norm` — Normalised volatility
- `price_change_1/3/6` — Short-term returns
- `volume_ratio` — Volume vs 20-period average
- `high_low_range` — Candle range
- `close_vs_ema20/50` — Price relative to trend
- `stoch_k`, `stoch_d` — Stochastic oscillator
- `williams_r` — Williams %R
- `adx` — Trend strength

## Quick Start (Local)

```bash
# 1. Clone and enter
git clone https://github.com/YOUR_USERNAME/forex-signal-platform
cd forex-signal-platform

# 2. Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your API keys
uvicorn app.main:app --reload

# 3. Frontend (new terminal)
cd frontend && npm install
cp .env.example .env.local  # add Supabase + backend URL
npm run dev
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full cloud deployment instructions.

## License

MIT — use freely for personal and commercial projects.
