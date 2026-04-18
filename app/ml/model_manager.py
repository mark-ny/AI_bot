"""
ModelManager — thread-safe singleton for serving XGBoost predictions.
Loads from disk on startup. Falls back gracefully if no model exists yet.
"""
import os
import pickle
import threading
from typing import Optional
import numpy as np
import pandas as pd

from app.ml.features import FEATURE_COLUMNS


class ModelManager:
    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._model  = None
        self._scaler = None
        self._model_lock = threading.Lock()
        self._ready  = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ModelManager()
        return cls._instance

    async def initialize(self):
        """Load model from disk on app startup. Trains a fresh one if none exists."""
        from app.config import get_settings
        settings = get_settings()
        model_path  = os.path.join(settings.model_path, "xgb_model.pkl")
        scaler_path = os.path.join(settings.model_path, "scaler.pkl")

        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.load(model_path, scaler_path)
            print("[model] Loaded existing model from disk")
        else:
            print("[model] No saved model found — will train on first scheduler run")

    def load(self, model_path: str, scaler_path: str):
        """Hot-reload model and scaler (called after retraining)."""
        with self._model_lock:
            with open(model_path,  "rb") as f: self._model  = pickle.load(f)
            with open(scaler_path, "rb") as f: self._scaler = pickle.load(f)
            self._ready = True

    def predict(self, features: pd.DataFrame) -> Optional[dict]:
        """
        Run inference on a single-row feature DataFrame.
        Returns {"direction": 0|1, "confidence": float} or None.
        """
        with self._model_lock:
            if not self._ready or self._model is None:
                return None

            try:
                X = features[FEATURE_COLUMNS].values
                X_scaled = self._scaler.transform(X)
                proba    = self._model.predict_proba(X_scaled)[0]
                direction   = int(np.argmax(proba))     # 0=SELL, 1=BUY
                confidence  = float(np.max(proba))
                return {"direction": direction, "confidence": confidence}
            except Exception as exc:
                print(f"[model] Prediction error: {exc}")
                return None
