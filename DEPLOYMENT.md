# ForexAI Platform — Complete Deployment Guide

## Prerequisites
- GitHub account (free)
- Supabase account (free at supabase.com)
- Render account (free at render.com)
- Vercel account (free at vercel.com)
- Twelve Data API key (free at twelvedata.com — 800 req/day)
- Optional: Telegram bot token (free via @BotFather)

---

## STEP 1: GitHub Repository

```bash
# 1. Create a new repo on github.com named: forex-signal-platform
# 2. Clone it locally and extract the project files into it

git clone https://github.com/YOUR_USERNAME/forex-signal-platform.git
cd forex-signal-platform

# Extract the downloaded tar.gz into this folder
tar -xzf forex-platform.tar.gz --strip-components=1

# Push everything
git add .
git commit -m "Initial commit — ForexAI platform"
git push origin main
```

---

## STEP 2: Supabase Setup

### 2a. Create project
1. Go to supabase.com → New Project
2. Name it `forex-signal-platform`
3. Set a strong database password (save it)
4. Choose region closest to your users
5. Wait ~2 minutes for provisioning

### 2b. Run the schema
1. Go to: SQL Editor → New Query
2. Open `supabase/schema.sql` from this repo
3. Paste the entire contents and click **Run**
4. You should see: "Success. No rows returned"

### 2c. Get your credentials
Go to: Project Settings → API

Copy these values (you'll need them in Steps 3 and 4):
```
SUPABASE_URL          = https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY     = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...   (anon/public)
SUPABASE_SERVICE_KEY  = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...   (service_role — keep secret!)
SUPABASE_JWT_SECRET   = your-jwt-secret                             (JWT Settings tab)
```

### 2d. Enable Realtime
1. Go to: Database → Replication
2. Under "Supabase Realtime", enable the `signals` table
3. This enables live signal push to the frontend

### 2e. Configure Auth
1. Go to: Authentication → URL Configuration
2. Set Site URL to your future Vercel URL (e.g. https://forex-ai.vercel.app)
3. Add to Redirect URLs: `https://forex-ai.vercel.app/**`
4. Optional: Enable Google OAuth under Providers

---

## STEP 3: Render Backend Deployment

### 3a. Connect GitHub
1. Go to render.com → New → Web Service
2. Connect your GitHub account
3. Select the `forex-signal-platform` repo
4. Set **Root Directory** to: `backend`

### 3b. Configure the service
```
Name:          forex-signal-backend
Region:        Oregon (US West)
Branch:        main
Runtime:       Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Plan:          Free
```

### 3c. Set environment variables
In Render → Environment tab, add these (one by one):

```
SUPABASE_URL           = https://xxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY   = eyJ...  (service_role key from Step 2c)
SUPABASE_JWT_SECRET    = your-jwt-secret
TWELVE_DATA_API_KEY    = your-twelve-data-key
ALPHA_VANTAGE_API_KEY  = your-alpha-vantage-key  (optional backup)
CORS_ORIGINS           = https://your-frontend.vercel.app
SECRET_KEY             = generate-a-random-32-char-string
ENVIRONMENT            = production
MODEL_PATH             = /tmp/models
TELEGRAM_BOT_TOKEN     = optional
TELEGRAM_CHAT_ID       = optional
```

To generate a SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3d. Deploy
1. Click **Create Web Service**
2. Wait for build (3-5 minutes on first deploy)
3. Your backend URL will be: `https://forex-signal-backend.onrender.com`
4. Test it: visit `https://forex-signal-backend.onrender.com/health`
   - Expected: `{"status": "ok", "version": "1.0.0"}`

### Important: Free Tier Cold Starts
Render free tier sleeps after 15 minutes of inactivity.
The first request after sleep takes ~30 seconds.
**Workaround**: Use UptimeRobot (free) to ping `/health` every 14 minutes.
1. Go to uptimerobot.com → Add Monitor
2. URL: `https://forex-signal-backend.onrender.com/health`
3. Interval: 14 minutes

---

## STEP 4: Vercel Frontend Deployment

### 4a. Connect GitHub
1. Go to vercel.com → New Project
2. Import the `forex-signal-platform` repo
3. Set **Root Directory** to: `frontend`
4. Framework: Next.js (auto-detected)

### 4b. Set environment variables
In Vercel → Settings → Environment Variables:

```
NEXT_PUBLIC_SUPABASE_URL       = https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY  = eyJ... (anon key from Step 2c)
NEXT_PUBLIC_API_URL            = https://forex-signal-backend.onrender.com
NEXT_PUBLIC_PAYPAL_CLIENT_ID   = your-paypal-client-id (optional)
```

### 4c. Deploy
1. Click **Deploy**
2. Build takes ~2 minutes
3. Your frontend URL will be: `https://forex-ai.vercel.app` (or similar)

### 4d. Update Supabase Auth redirect
1. Go back to Supabase → Authentication → URL Configuration
2. Update Site URL to your actual Vercel URL
3. Add your Vercel URL + `/**` to Redirect URLs

---

## STEP 5: Initial Model Training

The ML model must be trained before signals can be generated.
On first deploy, the backend will log "No saved model found".

**Option A: Wait for scheduler**
The daily retrain job at 02:00 UTC will train the model automatically.

**Option B: Trigger manually via API**
After deploying, call the signal generation endpoint to trigger training:
```bash
# First get a JWT token by signing up on your frontend
# Then call:
curl -X POST "https://forex-signal-backend.onrender.com/api/v1/signals/generate/EURUSD" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Option C: Train locally and push**
```bash
cd backend
cp .env.example .env
# Fill in your API keys
pip install -r requirements.txt
python ../scripts/train_model.py
# This saves models/ — commit and push if you want to pre-load
```

Note: On Render free tier, the model is stored at `/tmp/models` and resets on each cold start.
The daily retrain at 02:00 UTC will re-train after each restart — this is by design.

---

## STEP 6: Configure Telegram Alerts (Optional)

1. Message @BotFather on Telegram → `/newbot` → get your token
2. Create a channel, add your bot as admin
3. Get channel ID: message the bot, then visit:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in Render env vars
5. Redeploy — alerts fire automatically when signals are generated

---

## STEP 7: Get API Keys

### Twelve Data (primary — recommended)
1. Go to twelvedata.com → Sign Up (free)
2. Free tier: 800 API credits/day, 8 req/min
3. Get API key from dashboard
4. Set `TWELVE_DATA_API_KEY` in Render

### Alpha Vantage (backup)
1. Go to alphavantage.co → Get Free API Key
2. Free tier: 25 req/day
3. Set `ALPHA_VANTAGE_API_KEY` in Render

### PayPal (subscriptions)
1. Go to developer.paypal.com → Create App (free sandbox)
2. Create subscription plans in PayPal dashboard
3. Set `NEXT_PUBLIC_PAYPAL_CLIENT_ID` in Vercel
4. Update plan IDs in `frontend/app/subscribe/page.tsx`

---

## STEP 8: Verify Everything Works

Run this checklist:

```
□ Backend health check: GET /health returns {"status":"ok"}
□ Frontend loads: your-app.vercel.app shows login page
□ Auth: sign up with email, redirected to dashboard
□ Signal generation: trigger a signal, it appears in dashboard
□ Realtime: open dashboard in two tabs, new signal appears in both
□ Telegram: if configured, alert received in channel
□ Trade recording: click "Trade" on a signal, record lot size
□ Analytics: performance page shows stats
□ Daily retrain: check Render logs next morning at ~02:00 UTC
```

---

## Architecture Data Flow

```
User Browser
    │
    ├── Auth via Supabase Auth (JWT issued)
    │
    ├── Frontend (Vercel/Next.js)
    │       │
    │       ├── REST calls to Backend with JWT header
    │       └── Supabase Realtime subscription (WebSocket direct to Supabase)
    │
    └── Backend (Render/FastAPI)
            │
            ├── Validates JWT (Supabase JWT secret)
            ├── Fetches OHLCV from Twelve Data / Alpha Vantage
            ├── Runs ML model (XGBoost) for signal generation
            ├── Persists signals to Supabase
            ├── Sends Telegram alerts
            └── Scheduler: hourly signals + daily retrain at 02:00 UTC
```

---

## Free Tier Limits Summary

| Service      | Limit                          | Mitigation                        |
|--------------|--------------------------------|-----------------------------------|
| Render       | 750 hrs/month, sleeps 15 min   | UptimeRobot pings every 14 min    |
| Vercel       | 100GB bandwidth/month          | Adequate for most use cases       |
| Supabase     | 500MB DB, 2GB bandwidth        | Signals table stays small (<50MB) |
| Twelve Data  | 800 req/day, 8 req/min         | 10 pairs × 2 fetches = 20 req/hr  |
| Alpha Vantage| 25 req/day                     | Backup only                       |

---

## Common Errors and Fixes

### "No module named 'app'"
Ensure Root Directory is set to `backend` in Render (not the repo root).

### "Invalid JWT" on API calls
- Check `SUPABASE_JWT_SECRET` matches the JWT secret in Supabase dashboard
- Go to: Supabase → Settings → API → JWT Settings → JWT Secret

### Frontend shows blank page
- Check browser console for errors
- Verify all `NEXT_PUBLIC_*` env vars are set in Vercel
- Redeploy after setting env vars (required for Next.js)

### CORS errors
- Set `CORS_ORIGINS` in Render to your exact Vercel URL (no trailing slash)
- Example: `https://forex-ai.vercel.app`

### "Could not fetch OHLCV data"
- Check your Twelve Data API key is valid and has remaining credits
- Test directly: `https://api.twelvedata.com/time_series?symbol=EURUSD&interval=1h&apikey=YOUR_KEY`

### Model not predicting (returns None)
- Model hasn't been trained yet — wait for 02:00 UTC or trigger manually
- Check Render logs for "[model] Loaded existing model from disk"

### Supabase Realtime not working
- Ensure `supabase_realtime` publication includes the `signals` table (Step 2d)
- Check browser console for WebSocket connection errors

---

## Local Development Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in your keys
uvicorn app.main:app --reload
# Backend running at http://localhost:8000
# API docs at http://localhost:8000/docs

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local       # fill in your keys
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# Frontend running at http://localhost:3000
```

---

## Monitoring and Maintenance

### View backend logs
Render Dashboard → Your Service → Logs tab
Filter by: `[signal]`, `[trainer]`, `[scheduler]`, `[model]`

### Check model health
```bash
GET /api/v1/analytics/model-metrics
Authorization: Bearer <your-jwt>
```

### Manually retrain model
```bash
POST /api/v1/signals/generate/EURUSD
Authorization: Bearer <your-jwt>
```
This triggers training if no model exists.

### Monitor signal P&L
Run the outcome updater hourly:
```bash
python scripts/update_outcomes.py
```
Or add it to the Render scheduler (requires paid tier) / run locally with cron.
