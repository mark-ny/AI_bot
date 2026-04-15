/**
 * Typed API client for the FastAPI backend.
 * Automatically attaches the Supabase JWT to every request.
 */
import { createClient } from "./supabase";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getAuthHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const authHeaders = await getAuthHeader();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? "API request failed");
  }
  return res.json() as Promise<T>;
}

// ── Typed API methods ──────────────────────────────────────────

export const api = {
  signals: {
    list: (params?: { pair?: string; status?: string; limit?: number }) => {
      const qs = new URLSearchParams(
        Object.entries(params ?? {})
          .filter(([, v]) => v != null)
          .map(([k, v]) => [k, String(v)])
      ).toString();
      return apiFetch<Signal[]>(`/api/v1/signals${qs ? `?${qs}` : ""}`);
    },
    latest: () => apiFetch<Signal[]>("/api/v1/signals/latest"),
    generate: (pair: string, timeframe = "1h") =>
      apiFetch<Signal>(`/api/v1/signals/generate/${pair}?timeframe=${timeframe}`, {
        method: "POST",
      }),
    lotSize: (body: LotSizeRequest) =>
      apiFetch<LotSizeResponse>("/api/v1/signals/lot-size", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },
  trades: {
    list: () => apiFetch<Trade[]>("/api/v1/trades/"),
    open: (body: { signal_id: string; lot_size: number; notes?: string }) =>
      apiFetch<Trade>("/api/v1/trades/", { method: "POST", body: JSON.stringify(body) }),
    close: (tradeId: string, pnl_usd: number) =>
      apiFetch<Trade>(`/api/v1/trades/${tradeId}/close?pnl_usd=${pnl_usd}`, {
        method: "PATCH",
      }),
  },
  analytics: {
    performance: () => apiFetch<PerformanceStats>("/api/v1/analytics/performance"),
    modelMetrics: () => apiFetch<ModelMetric[]>("/api/v1/analytics/model-metrics"),
    userStats: () => apiFetch<UserStats>("/api/v1/analytics/user-stats"),
  },
  auth: {
    me: () => apiFetch<{ user: User; subscription: Subscription }>("/api/v1/auth/me"),
  },
};

// ── TypeScript types ───────────────────────────────────────────

export interface Signal {
  id: string;
  pair: string;
  direction: "BUY" | "SELL";
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  confidence: number;
  risk_reward: number;
  timeframe: string;
  status: "ACTIVE" | "TP_HIT" | "SL_HIT" | "EXPIRED";
  pnl_pips?: number;
  created_at: string;
  closed_at?: string;
}

export interface Trade {
  id: string;
  user_id: string;
  signal_id: string;
  lot_size: number;
  status: "OPEN" | "CLOSED" | "CANCELLED";
  pnl_usd?: number;
  opened_at: string;
  closed_at?: string;
  signals?: Signal;
}

export interface PerformanceStats {
  total_signals: number;
  win_rate: number;
  total_pips: number;
  avg_confidence: number;
  best_pair: string | null;
  current_drawdown: number;
  profit_factor: number;
}

export interface ModelMetric {
  id: string;
  model_version: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  training_samples: number;
  trained_at: string;
}

export interface UserStats {
  total_trades: number;
  total_pnl_usd: number;
  win_rate: number;
}

export interface LotSizeRequest {
  account_balance: number;
  risk_percent: number;
  stop_loss_pips: number;
  pair: string;
}

export interface LotSizeResponse {
  lot_size: number;
  risk_amount_usd: number;
  pip_value: number;
  max_loss_usd: number;
}

export interface User {
  id: string;
  email?: string;
  full_name?: string;
}

export interface Subscription {
  plan: "free" | "pro" | "premium";
  status: string;
  expires_at?: string;
}
