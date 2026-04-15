"use client";
import { TrendingUp, TrendingDown, Target, ShieldAlert, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Signal } from "@/lib/api";
import clsx from "clsx";

interface Props {
  signal: Signal;
  onTrade?: (signal: Signal) => void;
}

export default function SignalCard({ signal, onTrade }: Props) {
  const isBuy = signal.direction === "BUY";
  const conf  = Math.round(signal.confidence * 100);

  return (
    <div className="card hover:border-surface-500 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-base">{signal.pair}</span>
          <span className={isBuy ? "badge-buy" : "badge-sell"}>
            {signal.direction}
          </span>
          <span className="text-white/30 text-xs">{signal.timeframe}</span>
        </div>

        {/* Status badge */}
        <span
          className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", {
            "badge-active": signal.status === "ACTIVE",
            "badge-tp":     signal.status === "TP_HIT",
            "badge-sl":     signal.status === "SL_HIT",
            "bg-surface-600 text-white/40": signal.status === "EXPIRED",
          })}
        >
          {signal.status}
        </span>
      </div>

      {/* Price levels */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="text-center">
          <p className="text-white/40 text-xs mb-1">Entry</p>
          <p className="font-mono text-sm font-semibold">{signal.entry_price.toFixed(5)}</p>
        </div>
        <div className="text-center">
          <p className="text-red-400/70 text-xs mb-1 flex items-center justify-center gap-1">
            <ShieldAlert size={10} /> SL
          </p>
          <p className="font-mono text-sm text-red-400">{signal.stop_loss.toFixed(5)}</p>
        </div>
        <div className="text-center">
          <p className="text-brand-400/70 text-xs mb-1 flex items-center justify-center gap-1">
            <Target size={10} /> TP
          </p>
          <p className="font-mono text-sm text-brand-400">{signal.take_profit.toFixed(5)}</p>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-white/40 mb-1">
          <span>Confidence</span>
          <span className={clsx({
            "text-brand-400": conf >= 70,
            "text-yellow-400": conf >= 58 && conf < 70,
            "text-red-400": conf < 58,
          })}>{conf}%</span>
        </div>
        <div className="h-1.5 bg-surface-600 rounded-full overflow-hidden">
          <div
            className={clsx("h-full rounded-full transition-all", {
              "bg-brand-500": conf >= 70,
              "bg-yellow-500": conf >= 58 && conf < 70,
              "bg-red-500": conf < 58,
            })}
            style={{ width: `${conf}%` }}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-white/40 text-xs">
          <Clock size={11} />
          {formatDistanceToNow(new Date(signal.created_at), { addSuffix: true })}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-white/40">R:R {signal.risk_reward}</span>
          {signal.status === "ACTIVE" && onTrade && (
            <button
              onClick={() => onTrade(signal)}
              className="btn-primary text-xs py-1 px-3"
            >
              Trade
            </button>
          )}
        </div>
      </div>

      {/* P&L if closed */}
      {signal.pnl_pips != null && (
        <div className={clsx("mt-2 text-sm font-semibold", {
          "text-brand-400": signal.pnl_pips > 0,
          "text-red-400":   signal.pnl_pips <= 0,
        })}>
          {signal.pnl_pips > 0 ? "+" : ""}{signal.pnl_pips.toFixed(1)} pips
        </div>
      )}
    </div>
  );
}
