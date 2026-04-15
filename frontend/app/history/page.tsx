"use client";
import { useEffect, useState } from "react";
import { api, Trade } from "@/lib/api";
import Sidebar from "@/components/ui/Sidebar";
import { format } from "date-fns";
import { RefreshCw, TrendingUp, TrendingDown } from "lucide-react";
import toast from "react-hot-toast";
import clsx from "clsx";

export default function HistoryPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.trades.list();
      setTrades(data);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const totalPnL = trades.reduce((sum, t) => sum + (t.pnl_usd ?? 0), 0);
  const wins = trades.filter((t) => (t.pnl_usd ?? 0) > 0).length;
  const closed = trades.filter((t) => t.status === "CLOSED");

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur-md
                        border-b border-surface-600 px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">Trade History</h1>
            <p className="text-white/40 text-sm">All recorded trades</p>
          </div>
          <button onClick={load} className="btn-ghost text-xs flex items-center gap-1.5">
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Summary stats */}
          {closed.length > 0 && (
            <div className="grid grid-cols-3 gap-4">
              <div className="stat-card">
                <p className="text-white/50 text-xs">Total P&L</p>
                <p className={clsx("text-2xl font-bold", totalPnL >= 0 ? "text-brand-400" : "text-red-400")}>
                  {totalPnL >= 0 ? "+" : ""}${totalPnL.toFixed(2)}
                </p>
              </div>
              <div className="stat-card">
                <p className="text-white/50 text-xs">Win Rate</p>
                <p className="text-2xl font-bold">
                  {closed.length > 0 ? ((wins / closed.length) * 100).toFixed(0) : 0}%
                </p>
              </div>
              <div className="stat-card">
                <p className="text-white/50 text-xs">Total Trades</p>
                <p className="text-2xl font-bold">{trades.length}</p>
                <p className="text-white/40 text-xs">{closed.length} closed</p>
              </div>
            </div>
          )}

          {/* Trade table */}
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-600">
                  {["Pair", "Direction", "Lot", "Status", "P&L", "Opened", "Closed"].map((h) => (
                    <th key={h} className="text-left text-white/40 text-xs font-medium px-4 py-3">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-white/30">
                      <RefreshCw className="animate-spin mx-auto" size={20} />
                    </td>
                  </tr>
                ) : trades.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-white/30 text-sm">
                      No trades yet. Record a trade from the Signals page.
                    </td>
                  </tr>
                ) : (
                  trades.map((trade) => {
                    const sig = trade.signals;
                    const isBuy = sig?.direction === "BUY";
                    const pnl = trade.pnl_usd ?? null;

                    return (
                      <tr key={trade.id} className="border-b border-surface-700 hover:bg-surface-700/30">
                        <td className="px-4 py-3 font-medium">{sig?.pair ?? "—"}</td>
                        <td className="px-4 py-3">
                          {sig ? (
                            <span className={isBuy ? "badge-buy" : "badge-sell"}>
                              {sig.direction}
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-4 py-3 font-mono">{trade.lot_size}</td>
                        <td className="px-4 py-3">
                          <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", {
                            "bg-yellow-500/20 text-yellow-400": trade.status === "OPEN",
                            "bg-brand-500/20 text-brand-400":   trade.status === "CLOSED" && (pnl ?? 0) >= 0,
                            "bg-red-500/20 text-red-400":        trade.status === "CLOSED" && (pnl ?? 0) < 0,
                          })}>
                            {trade.status}
                          </span>
                        </td>
                        <td className={clsx("px-4 py-3 font-mono font-medium", {
                          "text-brand-400": (pnl ?? 0) > 0,
                          "text-red-400":   (pnl ?? 0) < 0,
                          "text-white/30":  pnl == null,
                        })}>
                          {pnl != null ? `${pnl >= 0 ? "+" : ""}$${pnl.toFixed(2)}` : "—"}
                        </td>
                        <td className="px-4 py-3 text-white/50 text-xs">
                          {format(new Date(trade.opened_at), "MMM d, HH:mm")}
                        </td>
                        <td className="px-4 py-3 text-white/50 text-xs">
                          {trade.closed_at
                            ? format(new Date(trade.closed_at), "MMM d, HH:mm")
                            : "—"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
