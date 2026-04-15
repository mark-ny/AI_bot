import { create } from "zustand";
import type { Signal, PerformanceStats, Subscription } from "./api";

interface AppState {
  signals: Signal[];
  performance: PerformanceStats | null;
  subscription: Subscription | null;
  isLoading: boolean;

  setSignals: (signals: Signal[]) => void;
  addSignal: (signal: Signal) => void;
  setPerformance: (p: PerformanceStats) => void;
  setSubscription: (s: Subscription) => void;
  setLoading: (v: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  signals: [],
  performance: null,
  subscription: null,
  isLoading: false,

  setSignals:      (signals)      => set({ signals }),
  addSignal:       (signal)       => set((s) => ({ signals: [signal, ...s.signals] })),
  setPerformance:  (performance)  => set({ performance }),
  setSubscription: (subscription) => set({ subscription }),
  setLoading:      (isLoading)    => set({ isLoading }),
}));
