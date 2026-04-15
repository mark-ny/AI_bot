"use client";
import { useEffect, useState } from "react";
import { api, Signal } from "@/lib/api";
import Sidebar from "@/components/ui/Sidebar";
import SignalCard from "@/components/ui/SignalCard";
import TradeModal from "@/components/ui/TradeModal";
import { RefreshCw, Plus } from "lucide-react";
import toast from "react-hot-toast";
import clsx from "clsx";

const PAIRS = [
  "ALL", "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
  "USD/CAD", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY",
];
const STATUSES = ["ALL", "ACTIVE", "TP_HIT", "SL_HIT", "EXPIRED"];
const DIRECTIONS = ["ALL", "BUY", "SELL"];

export default function SignalsPage() {
  const [signals, setSignals]       = useState<Signal[]>([]);
  const [loading, setLoading]       = useState(true);
  const [generating, setGenerating] = useState(false);
  const [pair, setPair]             = useState("ALL");
  const [status, setStatus]         = useState("ALL");
  const [direction, setDirection]   = useState("ALL");
  const [tradeSignal, setTradeSignal] = useState<Signal | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.signals.list({
        pair:      pair !== "ALL" ? pair : undefined,
        status:    status !== "ALL" ? status : undefined,
        direction: direction !== "ALL" ? direction : undefined,
        limit:     100,
      });
      setSignals(data);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [pair, status, direction]);

  const generateSignal = async () => {
    if (pair === "ALL") {
      toast.error("Select a specific pair to generate a signal");
      return;
    }
    setGenerating(true);
    try {
      const sig = await api.signals.generate(pair);
      setSignals((prev) => [sig, ...prev]);
      toast.success(`Signal generated: ${sig.direction} ${sig.pair}`);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setGenerating(false);
    }
  };

  function FilterPill({
    value, selected, onClick,
  }: { value: string; selected: boolean; onClick: () => void }) {
    return (
      <button
        onClick={onClick}
        className={clsx(
          "px-3 py-1 rounded-full text-xs font-medium transition-colors",
          selected
            ? "bg-brand-600 text-white"
            : "bg-surface-700 text-white/50 hover:text-white"
        )}
      >
        {value}
      </button>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur-md
                        border-b border-surface-600 px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-lg font-semibold">Signals</h1>
            <div className="flex items-center gap-2">
              <button onClick={load} className="btn-ghost text-xs flex items-center gap-1.5">
                <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
                Refresh
              </button>
              <button
                onClick={generateSignal}
                disabled={generating}
                className="btn-primary text-xs flex items-center gap-1.5"
              >
                <Plus size={13} />
                {generating ? "Generating..." : "Generate"}
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div>
              <p className="text-white/30 text-xs mb-1.5">Pair</p>
              <div className="flex flex-wrap gap-1">
                {PAIRS.map((p) => (
                  <FilterPill key={p} value={p} selected={pair === p} onClick={() => setPair(p)} />
                ))}
              </div>
            </div>
            <div>
              <p className="text-white/30 text-xs mb-1.5">Direction</p>
              <div className="flex gap-1">
                {DIRECTIONS.map((d) => (
                  <FilterPill key={d} value={d} selected={direction === d} onClick={() => setDirection(d)} />
                ))}
              </div>
            </div>
            <div>
              <p className="text-white/30 text-xs mb-1.5">Status</p>
              <div className="flex flex-wrap gap-1">
                {STATUSES.map((s) => (
                  <FilterPill key={s} value={s} selected={status === s} onClick={() => setStatus(s)} />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Signals grid */}
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center py-20">
              <RefreshCw className="animate-spin text-white/30" size={24} />
            </div>
          ) : signals.length === 0 ? (
            <div className="card text-center py-20 text-white/30">
              <p>No signals match your filters.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {signals.map((s) => (
                <SignalCard
                  key={s.id}
                  signal={s}
                  onTrade={s.status === "ACTIVE" ? setTradeSignal : undefined}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {tradeSignal && (
        <TradeModal signal={tradeSignal} onClose={() => setTradeSignal(null)} />
      )}
    </div>
  );
}
