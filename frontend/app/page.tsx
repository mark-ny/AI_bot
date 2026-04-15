"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/ui/AuthProvider";
import { Zap } from "lucide-react";

export default function HomePage() {
  const { session, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      router.replace(session ? "/dashboard" : "/auth");
    }
  }, [session, loading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-900">
      <div className="flex flex-col items-center gap-4 text-white/30">
        <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center animate-pulse">
          <Zap size={24} className="text-white" />
        </div>
        <span className="text-sm">Loading ForexAI...</span>
      </div>
    </div>
  );
}
