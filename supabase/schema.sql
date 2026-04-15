-- ============================================================
-- Forex Signal Platform — Supabase PostgreSQL Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Enable UUID extension (already enabled on Supabase by default)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 1. USERS ─────────────────────────────────────────────────
-- Mirrors auth.users; add profile columns here.
CREATE TABLE IF NOT EXISTS public.users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT,
    full_name   TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── 2. SUBSCRIPTIONS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    plan        TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'premium')),
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    expires_at  TIMESTAMPTZ,
    paypal_subscription_id TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user ON public.subscriptions(user_id);

CREATE TRIGGER trg_subscriptions_updated_at
BEFORE UPDATE ON public.subscriptions
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── 3. SIGNALS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.signals (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pair         TEXT NOT NULL,
    direction    TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    entry_price  NUMERIC(18, 6) NOT NULL,
    stop_loss    NUMERIC(18, 6) NOT NULL,
    take_profit  NUMERIC(18, 6) NOT NULL,
    confidence   NUMERIC(5, 4)  NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    risk_reward  NUMERIC(5, 2)  NOT NULL,
    timeframe    TEXT NOT NULL DEFAULT '1h',
    status       TEXT NOT NULL DEFAULT 'ACTIVE'
                 CHECK (status IN ('ACTIVE', 'TP_HIT', 'SL_HIT', 'EXPIRED')),
    pnl_pips     NUMERIC(10, 2),
    closed_at    TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signals_pair       ON public.signals(pair);
CREATE INDEX idx_signals_status     ON public.signals(status);
CREATE INDEX idx_signals_created_at ON public.signals(created_at DESC);
CREATE INDEX idx_signals_direction  ON public.signals(direction);

-- ── 4. TRADES ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.trades (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    signal_id   UUID NOT NULL REFERENCES public.signals(id) ON DELETE CASCADE,
    lot_size    NUMERIC(10, 2) NOT NULL,
    notes       TEXT,
    status      TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED')),
    pnl_usd     NUMERIC(12, 2),
    opened_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at   TIMESTAMPTZ
);

CREATE INDEX idx_trades_user_id   ON public.trades(user_id);
CREATE INDEX idx_trades_signal_id ON public.trades(signal_id);
CREATE INDEX idx_trades_status    ON public.trades(status);

-- ── 5. MODEL METRICS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.model_metrics (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_version    TEXT NOT NULL,
    accuracy         NUMERIC(6, 4) NOT NULL,
    precision        NUMERIC(6, 4) NOT NULL,
    recall           NUMERIC(6, 4) NOT NULL,
    f1_score         NUMERIC(6, 4) NOT NULL,
    training_samples INTEGER NOT NULL,
    trained_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_model_metrics_trained ON public.model_metrics(trained_at DESC);

-- ── ROW LEVEL SECURITY (RLS) ──────────────────────────────────
-- Enable RLS on all user-data tables
ALTER TABLE public.users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.signals        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_metrics  ENABLE ROW LEVEL SECURITY;

-- Users: can only read/update their own profile
CREATE POLICY "users_self_read"   ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_self_update" ON public.users FOR UPDATE USING (auth.uid() = id);

-- Subscriptions: own row only
CREATE POLICY "subs_self"         ON public.subscriptions FOR ALL USING (auth.uid() = user_id);

-- Trades: own rows only
CREATE POLICY "trades_self"       ON public.trades FOR ALL USING (auth.uid() = user_id);

-- Signals: all authenticated users can read (it's a broadcast product)
CREATE POLICY "signals_auth_read" ON public.signals FOR SELECT
    USING (auth.role() = 'authenticated');

-- Model metrics: all authenticated users can read
CREATE POLICY "metrics_auth_read" ON public.model_metrics FOR SELECT
    USING (auth.role() = 'authenticated');

-- Backend service role bypasses RLS automatically (uses service key)

-- ── REALTIME ─────────────────────────────────────────────────
-- Enable realtime publication for the signals table
-- (Supabase Realtime channels)
ALTER PUBLICATION supabase_realtime ADD TABLE public.signals;

-- ── SAMPLE DATA (optional — for testing UI) ──────────────────
-- INSERT INTO public.signals (pair, direction, entry_price, stop_loss, take_profit, confidence, risk_reward, timeframe, status)
-- VALUES
--   ('EUR/USD', 'BUY',  1.08512, 1.08200, 1.09100, 0.7234, 2.0, '1h', 'ACTIVE'),
--   ('GBP/USD', 'SELL', 1.27340, 1.27680, 1.26650, 0.6812, 2.03, '1h', 'ACTIVE'),
--   ('USD/JPY', 'BUY',  149.820, 149.200, 151.100, 0.6521, 2.13, '4h', 'TP_HIT');
