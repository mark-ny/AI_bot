"use client";
import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from "recharts";
import { api, PerformanceStats, ModelMetric } from "@/lib/api";
import Sidebar from "@/components/ui/Sidebar";
import { format } from "date-fns";
import { Brain, TrendingUp } from "lucide-react";
import toast from "react-hot-toast";

const CHART_THEME = {
  grid:    "#2a2a3a",
  text:    "#6b7280",
  green:   "#22c55e",
  red:     "#ef4444",
  blue:    "#3b82f6",
  purple:  "#a855f7",
};

const CustomTooltipStyle = {
  backgroundColor: "#1a1a24",
  border: "1px solid #2a2a3a",
  borderRadius: 8,
  color: "#fff",
  fontSize: 12,
};

export default function AnalyticsPage() {
  const [stats, setStats]     = useState<PerformanceStats | null>(null);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.analytics.performance(), api.analytics.modelMetrics()])
      .then(([s, m]) => { setStats(s); setMetrics(m); })
      .catch((err) => toast.error(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Chart data from model metrics history
  const modelChartData = [...metrics].reverse().map((m) => ({
    date:     format(new Date(m.trained_at), "MMM d"),
    accuracy: +(m.accuracy * 100).toFixed(1),
    f1:       +(m.f1_score * 100).toFixed(1),
    precision:+(m.precision * 100).toFixed(1),
    recall:   +(m.recall * 100).toFixed(1),
    samples:  m.training_samples,
  }));

  // Summary stat cards
  const summaryItems = stats ? [
    { label: "Win Rate",        value: `${(stats.win_rate * 100).toFixed(1)}%`,       color: "text-brand-400" },
    { label: "Total Pips",      value: `${stats.total_pips >= 0 ? "+" : ""}${stats.total_pips.toFixed(0)}`, color: stats.total_pips >= 0 ? "text-brand-400" : "text-red-400" },
    { label: "Profit Factor",   value: stats.profit_factor.toFixed(2),                 color: "text-white" },
    { label: "Avg Confidence",  value: `${(stats.avg_confidence * 100).toFixed(1)}%`,  color: "text-white" },
    { label: "Max Drawdown",    value: `${stats.current_drawdown.toFixed(0)} pips`,    color: "text-red-400" },
    { label: "Best Pair",       value: stats.best_pair ?? "N/A",                       color: "text-blue-400" },
  ] : [];

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur-md
                        border-b border-surface-600 px-6 py-4">
          <h1 className="text-lg font-semibold">Analytics</h1>
          <p className="text-white/40 text-sm">Signal performance & ML model health</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Performance summary */}
          <div>
            <h2 className="text-sm font-semibold text-white/60 mb-3 flex items-center gap-2">
              <TrendingUp size={14} /> Performance Overview
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {summaryItems.map((item) => (
                <div key={item.label} className="stat-card">
                  <p className="text-white/40 text-xs">{item.label}</p>
                  <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Win rate doughnut approximation — simple bar chart */}
          {stats && (
            <div className="card">
              <h3 className="text-sm font-semibold mb-4">Signal Outcome Breakdown</h3>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={[
                  { name: "TP Hit",  value: Math.round(stats.win_rate * stats.total_signals) },
                  { name: "SL Hit",  value: Math.round((1 - stats.win_rate) * stats.total_signals * 0.7) },
                  { name: "Expired", value: Math.round((1 - stats.win_rate) * stats.total_signals * 0.3) },
                ]} barSize={36}>
                  <XAxis dataKey="name" tick={{ fill: CHART_THEME.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: CHART_THEME.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={CustomTooltipStyle} cursor={{ fill: "#2a2a3a" }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}
                    fill={CHART_THEME.green}
                    label={{ position: "top", fill: CHART_THEME.text, fontSize: 11 }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* ML model metrics over time */}
          {modelChartData.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold mb-1 flex items-center gap-2">
                <Brain size={14} className="text-purple-400" />
                ML Model Performance Over Time
              </h3>
              <p className="text-white/30 text-xs mb-4">Daily retrain metrics (walk-forward CV)</p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={modelChartData}>
                  <CartesianGrid stroke={CHART_THEME.grid} strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: CHART_THEME.text, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[40, 100]} tick={{ fill: CHART_THEME.text, fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
                  <Tooltip contentStyle={CustomTooltipStyle} formatter={(v: number) => `${v}%`} />
                  <Legend wrapperStyle={{ fontSize: 12, color: CHART_THEME.text }} />
                  <Line type="monotone" dataKey="accuracy"  stroke={CHART_THEME.green}  strokeWidth={2} dot={false} name="Accuracy" />
                  <Line type="monotone" dataKey="f1"        stroke={CHART_THEME.blue}   strokeWidth={2} dot={false} name="F1 Score" />
                  <Line type="monotone" dataKey="precision" stroke={CHART_THEME.purple} strokeWidth={2} dot={false} name="Precision" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Latest model metrics table */}
          {metrics.length > 0 && (
            <div className="card overflow-x-auto p-0">
              <div className="px-5 py-4 border-b border-surface-600">
                <h3 className="text-sm font-semibold">Model Training Log</h3>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-700">
                    {["Version", "Accuracy", "Precision", "Recall", "F1", "Samples", "Trained"].map(h => (
                      <th key={h} className="text-left text-white/40 text-xs font-medium px-4 py-3">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m) => (
                    <tr key={m.id} className="border-b border-surface-700 hover:bg-surface-700/30">
                      <td className="px-4 py-2.5 font-mono text-xs text-white/70">{m.model_version}</td>
                      <td className="px-4 py-2.5 text-brand-400">{(m.accuracy * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2.5">{(m.precision * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2.5">{(m.recall * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2.5 text-blue-400">{(m.f1_score * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2.5 font-mono text-xs">{m.training_samples.toLocaleString()}</td>
                      <td className="px-4 py-2.5 text-white/40 text-xs">
                        {format(new Date(m.trained_at), "MMM d, HH:mm")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
