/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";
import { useEffect, useState, useCallback } from "react";
import { api, Signal, PerformanceStats } from "@/lib/api";
import { createClient } from "@/lib/supabase";
import SignalCard from "@/components/ui/SignalCard";
import Sidebar from "@/components/ui/Sidebar";
import TradeModal from "@/components/ui/TradeModal";
import { RefreshCw, Wifi, WifiOff } from "lucide-react";
import toast from "react-hot-toast";
import clsx from "clsx";

function StatCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className="stat-card">
      <p className="text-white/50 text-xs">{label}</p>
      <p className={clsx("text-2xl font-bold", accent ?? "text-white")}>{value}</p>
      {sub && <p className="text-white/40 text-xs">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [tradeSignal, setTradeSignal] = useState<Signal | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [sigs, perf] = await Promise.all([
        api.signals.latest(),
        api.analytics.performance(),
      ]);
      setSignals(sigs);
      setStats(perf);
    } catch (err: any) {
      toast.error(err.message ?? "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel("signals-live")
      .on(
        "postgres_changes" as any,
        { event: "INSERT", schema: "public", table: "signals" },
        (payload: any) => {
          const newSignal = payload.new as Signal;
          setSignals((prev) => [newSignal, ...prev.slice(0, 19)]);
          toast.success(`New signal: ${newSignal.direction} ${newSignal.pair}`, {
            icon: newSignal.direction === "BUY" ? "📈" : "📉",
          });
        }
      )
      .subscribe((status: string) => {
        setWsConnected(status === "SUBSCRIBED");
      });
    return () => { supabase.removeChannel(channel); };
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <RefreshCw className="animate-spin text-white/40" size={24} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur-md border-b border-surface-600 px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">Dashboard</h1>
            <p className="text-white/40 text-sm">Live AI-generated forex signals</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={clsx("flex items-center gap-1.5 text-xs", wsConnected ? "text-brand-400" : "text-white/30")}>
              {wsConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
              {wsConnected ? "Live" : "Offline"}
            </span>
            <button onClick={loadData} className="btn-ghost text-xs flex items-center gap-1.5">
              <RefreshCw size={13} /> Refresh
            </button>
          </div>
        </div>
        <div className="p-6 space-y-6">
          {stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatCard label="Win Rate" value={`${(stats.win_rate * 100).toFixed(1)}%`} sub={`${stats.total_signals} signals`} accent={stats.win_rate >= 0.55 ? "text-brand-400" : "text-yellow-400"} />
              <StatCard label="Total Pips" value={stats.total_pips >= 0 ? `+${stats.total_pips.toFixed(0)}` : `${stats.total_pips.toFixed(0)}`} sub="All time" accent={stats.total_pips >= 0 ? "text-brand-400" : "text-red-400"} />
              <StatCard label="Avg Confidence" value={`${(stats.avg_confidence * 100).toFixed(1)}%`} sub="ML model score" />
              <StatCard label="Profit Factor" value={stats.profit_factor.toFixed(2)} sub={`Best: ${stats.best_pair ?? "N/A"}`} accent={stats.profit_factor >= 1.5 ? "text-brand-400" : "text-yellow-400"} />
            </div>
          )}
          <div>
            <h2 className="font-semibold mb-4">Active Signals ({signals.filter(s => s.status === "ACTIVE").length} live)</h2>
            {signals.length === 0 ? (
              <div className="card text-center py-16 text-white/30">
                <p className="text-sm">No signals yet. Check back soon.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {signals.map((signal) => (
                  <SignalCard key={signal.id} signal={signal} onTrade={signal.status === "ACTIVE" ? setTradeSignal : undefined} />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
      {tradeSignal && <TradeModal signal={tradeSignal} onClose={() => setTradeSignal(null)} />}
    </div>
  );
}
