"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, History,
  BarChart3, CreditCard, LogOut, Zap,
} from "lucide-react";
import { useAuth } from "./AuthProvider";
import clsx from "clsx";

const navItems = [
  { href: "/dashboard",  icon: LayoutDashboard, label: "Dashboard"  },
  { href: "/signals",    icon: TrendingUp,       label: "Signals"    },
  { href: "/history",    icon: History,          label: "History"    },
  { href: "/analytics",  icon: BarChart3,        label: "Analytics"  },
  { href: "/subscribe",  icon: CreditCard,       label: "Upgrade"    },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { signOut, user } = useAuth();

  return (
    <aside className="w-56 shrink-0 bg-surface-800 border-r border-surface-600
                      flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5 border-b border-surface-600">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
          <Zap size={16} className="text-white" />
        </div>
        <span className="font-semibold text-white tracking-tight">ForexAI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              pathname === href
                ? "bg-brand-600/20 text-brand-400"
                : "text-white/60 hover:text-white hover:bg-surface-700"
            )}
          >
            <Icon size={17} />
            {label}
          </Link>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-4 py-4 border-t border-surface-600">
        <p className="text-xs text-white/40 truncate mb-3">
          {user?.email ?? "Loading..."}
        </p>
        <button
          onClick={signOut}
          className="flex items-center gap-2 text-sm text-white/50
                     hover:text-white transition-colors"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
