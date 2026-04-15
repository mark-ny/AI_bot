"use client";
import { useState } from "react";
import Sidebar from "@/components/ui/Sidebar";
import { Check, Zap } from "lucide-react";
import clsx from "clsx";

const plans = [
  {
    name:  "Free",
    price: "$0",
    per:   "forever",
    color: "border-surface-600",
    badge: null,
    features: [
      "5 signals per day",
      "EUR/USD, GBP/USD only",
      "1h timeframe",
      "Basic dashboard",
    ],
    cta:     "Current plan",
    ctaCls:  "btn-ghost w-full opacity-50 cursor-not-allowed",
    paypalId: null,
  },
  {
    name:  "Pro",
    price: "$19",
    per:   "per month",
    color: "border-brand-600",
    badge: "Most popular",
    features: [
      "Unlimited signals",
      "All 10 currency pairs",
      "1h, 4h timeframes",
      "Telegram alerts",
      "Trade journal",
      "Risk calculator",
    ],
    cta:     "Upgrade to Pro",
    ctaCls:  "btn-primary w-full",
    paypalId: "YOUR_PAYPAL_PLAN_ID_PRO",
  },
  {
    name:  "Premium",
    price: "$49",
    per:   "per month",
    color: "border-purple-600",
    badge: "Best value",
    features: [
      "Everything in Pro",
      "API access",
      "Model metrics dashboard",
      "Priority support",
      "Custom pair requests",
      "Early feature access",
    ],
    cta:     "Go Premium",
    ctaCls:  "w-full py-2 rounded-lg bg-purple-700 hover:bg-purple-600 text-white font-medium transition-colors",
    paypalId: "YOUR_PAYPAL_PLAN_ID_PREMIUM",
  },
];

declare global {
  interface Window { paypal?: any; }
}

export default function SubscribePage() {
  const [selected, setSelected] = useState<string | null>(null);

  const handleSubscribe = (plan: typeof plans[0]) => {
    if (!plan.paypalId) return;

    // PayPal subscription button — opens PayPal hosted checkout
    const paypalClientId = process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID;
    if (!paypalClientId) {
      alert("PayPal is not configured. Set NEXT_PUBLIC_PAYPAL_CLIENT_ID in your .env file.");
      return;
    }

    // Open PayPal subscription flow
    const url = `https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=${plan.paypalId}`;
    window.open(url, "_blank");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur-md
                        border-b border-surface-600 px-6 py-4">
          <h1 className="text-lg font-semibold">Upgrade Plan</h1>
          <p className="text-white/40 text-sm">Unlock more signals and features</p>
        </div>

        <div className="p-6 max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold mb-2">Simple, transparent pricing</h2>
            <p className="text-white/50">Cancel anytime. No hidden fees.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={clsx(
                  "bg-surface-800 border-2 rounded-2xl p-6 flex flex-col",
                  plan.color
                )}
              >
                {plan.badge && (
                  <span className="text-xs font-semibold bg-brand-600/20 text-brand-400
                                   px-2 py-0.5 rounded-full w-fit mb-3">
                    {plan.badge}
                  </span>
                )}

                <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-white/40 text-sm ml-1">/{plan.per}</span>
                </div>

                <ul className="space-y-2 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check size={15} className="text-brand-400 mt-0.5 shrink-0" />
                      <span className="text-white/80">{f}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSubscribe(plan)}
                  disabled={!plan.paypalId}
                  className={plan.ctaCls}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>

          <p className="text-center text-white/30 text-xs mt-8">
            Payments processed securely via PayPal. You can cancel your subscription at any time
            from your PayPal account.
          </p>
        </div>
      </main>
    </div>
  );
}
