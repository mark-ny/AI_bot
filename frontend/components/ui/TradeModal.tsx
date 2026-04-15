"use client";
import { useState } from "react";
import { api, Signal, LotSizeResponse } from "@/lib/api";
import { X, Calculator } from "lucide-react";
import toast from "react-hot-toast";

interface Props {
  signal: Signal;
  onClose: () => void;
}

export default function TradeModal({ signal, onClose }: Props) {
  const [lotSize, setLotSize]     = useState("0.01");
  const [balance, setBalance]     = useState("1000");
  const [riskPct, setRiskPct]     = useState("1");
  const [calc, setCalc]           = useState<LotSizeResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const slPips = Math.abs(signal.entry_price - signal.stop_loss) * 10_000;

  const runCalculator = async () => {
    try {
      const res = await api.signals.lotSize({
        account_balance: parseFloat(balance),
        risk_percent:    parseFloat(riskPct),
        stop_loss_pips:  slPips,
        pair:            signal.pair,
      });
      setCalc(res);
      setLotSize(res.lot_size.toString());
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const openTrade = async () => {
    setSubmitting(true);
    try {
      await api.trades.open({
        signal_id: signal.id,
        lot_size:  parseFloat(lotSize),
      });
      toast.success("Trade recorded!");
      onClose();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const isBuy = signal.direction === "BUY";

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-surface-800 border border-surface-600 rounded-2xl w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{signal.pair}</span>
            <span className={isBuy ? "badge-buy" : "badge-sell"}>{signal.direction}</span>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Signal summary */}
          <div className="grid grid-cols-3 gap-3 bg-surface-700 rounded-lg p-3">
            <div className="text-center">
              <p className="text-white/40 text-xs">Entry</p>
              <p className="font-mono text-sm font-semibold">{signal.entry_price.toFixed(5)}</p>
            </div>
            <div className="text-center">
              <p className="text-red-400/70 text-xs">Stop Loss</p>
              <p className="font-mono text-sm text-red-400">{signal.stop_loss.toFixed(5)}</p>
            </div>
            <div className="text-center">
              <p className="text-brand-400/70 text-xs">Take Profit</p>
              <p className="font-mono text-sm text-brand-400">{signal.take_profit.toFixed(5)}</p>
            </div>
          </div>

          {/* Lot size calculator */}
          <div className="space-y-3">
            <p className="text-sm font-medium flex items-center gap-1.5">
              <Calculator size={14} className="text-brand-400" />
              Risk Calculator
            </p>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-white/50 mb-1 block">Account Balance ($)</label>
                <input
                  className="input"
                  type="number"
                  value={balance}
                  onChange={(e) => setBalance(e.target.value)}
                  min="0"
                  step="100"
                />
              </div>
              <div>
                <label className="text-xs text-white/50 mb-1 block">Risk % per trade</label>
                <input
                  className="input"
                  type="number"
                  value={riskPct}
                  onChange={(e) => setRiskPct(e.target.value)}
                  min="0.1"
                  max="10"
                  step="0.5"
                />
              </div>
            </div>
            <button onClick={runCalculator} className="btn-ghost w-full text-sm">
              Calculate lot size
            </button>

            {calc && (
              <div className="bg-surface-700 rounded-lg p-3 text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-white/50">Recommended lot size</span>
                  <span className="font-mono font-semibold text-brand-400">{calc.lot_size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/50">Risk amount</span>
                  <span className="font-mono">${calc.risk_amount_usd.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/50">Max loss</span>
                  <span className="font-mono text-red-400">${calc.max_loss_usd.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/50">SL distance</span>
                  <span className="font-mono">{slPips.toFixed(1)} pips</span>
                </div>
              </div>
            )}
          </div>

          {/* Manual lot size override */}
          <div>
            <label className="text-xs text-white/50 mb-1 block">Lot size to record</label>
            <input
              className="input"
              type="number"
              value={lotSize}
              onChange={(e) => setLotSize(e.target.value)}
              min="0.01"
              step="0.01"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="px-5 pb-5 flex gap-2">
          <button onClick={onClose} className="btn-ghost flex-1">
            Cancel
          </button>
          <button
            onClick={openTrade}
            disabled={submitting}
            className="btn-primary flex-1"
          >
            {submitting ? "Recording..." : "Record Trade"}
          </button>
        </div>
      </div>
    </div>
  );
}
