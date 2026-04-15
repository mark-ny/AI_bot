"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { createClient } from "@/lib/supabase";
import { useAuth } from "@/components/ui/AuthProvider";
import { Zap } from "lucide-react";

export default function AuthPage() {
  const supabase = createClient();
  const { session } = useAuth();
  const router = useRouter();

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (session) router.replace("/dashboard");
  }, [session, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-900 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
            <Zap size={20} className="text-white" />
          </div>
          <span className="text-2xl font-bold tracking-tight">ForexAI</span>
        </div>

        <p className="text-center text-white/50 text-sm mb-6">
          AI-powered forex signals, updated every hour
        </p>

        {/* Auth form */}
        <div className="bg-surface-800 border border-surface-600 rounded-2xl p-6">
          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand:        "#16a34a",
                    brandAccent:  "#22c55e",
                    inputBackground: "#22222f",
                    inputText:    "#ffffff",
                    inputBorder:  "#2a2a3a",
                    inputBorderFocus: "#16a34a",
                    inputBorderHover: "#3a3a4a",
                    defaultButtonBackground: "#22222f",
                    defaultButtonBackgroundHover: "#2a2a3a",
                    defaultButtonText: "#ffffff",
                  },
                  radii: {
                    borderRadiusButton: "8px",
                    buttonBorderRadius: "8px",
                    inputBorderRadius:  "8px",
                  },
                  space: {
                    inputPadding: "10px 14px",
                    buttonPadding: "10px 14px",
                  },
                },
              },
            }}
            providers={["google"]}
            redirectTo={`${typeof window !== "undefined" ? window.location.origin : ""}/dashboard`}
          />
        </div>

        <p className="text-center text-white/30 text-xs mt-4">
          Free plan includes 5 signals per day. No credit card required.
        </p>
      </div>
    </div>
  );
}
