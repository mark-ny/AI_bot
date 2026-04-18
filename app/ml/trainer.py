"""
Model trainer — trains XGBoost on historical forex data for all pairs,
evaluates with time-series walk-forward split, stores metrics in Supabase.
Called by the daily scheduler at 02:00 UTC.
"""
import os
import uuid
import pickle
import asyncio
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from app.ml.features import compute_features, label_direction, FEATURE_COLUMNS
from app.services.data_service import get_ohlcv, SUPPORTED_PAIRS
from app.database import get_supabase
from app.ml.model_manager import ModelManager
from app.config import get_settings


async def _collect_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """
    Collect OHLCV for all pairs + timeframes, compute features and labels.
    Returns (X, y) for model training.
    """
    all_X = []
    all_y = []

    # Fetch multiple timeframes for richer signal
    timeframes = ["1h", "4h"]

    for pair in SUPPORTED_PAIRS:
        for tf in timeframes:
            try:
                df = await get_ohlcv(pair, interval=tf, bars=500)
                features = compute_features(df)
                labels   = label_direction(df).loc[features.index]

                # Align and drop NaN
                valid = features.join(labels.rename("label")).dropna()
                # Drop future-looking rows (last 3 bars have no valid label)
                valid = valid.iloc[:-3]

                if len(valid) < 30:
                    continue

                all_X.append(valid[FEATURE_COLUMNS])
                all_y.append(valid["label"])
                print(f"[trainer] {pair} {tf}: {len(valid)} samples")

            except Exception as exc:
                print(f"[trainer] Skipping {pair} {tf}: {exc}")

    if not all_X:
        raise RuntimeError("No training data collected — check API keys")

    X = pd.concat(all_X, ignore_index=True)
    y = pd.concat(all_y, ignore_index=True)
    return X, y


def _train_xgboost(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Train XGBoost with time-series cross-validation.
    Returns (model, scaler, metrics_dict).
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Walk-forward CV to simulate live trading conditions
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = {"accuracy": [], "precision": [], "recall": [], "f1": []}

    for train_idx, val_idx in tscv.split(X_scaled):
        X_tr, X_val = X_scaled[train_idx], X_scaled[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        preds = model.predict(X_val)

        cv_scores["accuracy"].append(accuracy_score(y_val, preds))
        cv_scores["precision"].append(precision_score(y_val, preds, zero_division=0))
        cv_scores["recall"].append(recall_score(y_val, preds, zero_division=0))
        cv_scores["f1"].append(f1_score(y_val, preds, zero_division=0))

    # Final model trained on all data
    final_model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    final_model.fit(X_scaled, y, verbose=False)

    metrics = {k: float(np.mean(v)) for k, v in cv_scores.items()}
    metrics["training_samples"] = len(y)
    return final_model, scaler, metrics


async def train_and_save():
    """
    Full pipeline: collect data → train → save model → update Supabase metrics.
    Called by daily scheduler.
    """
    settings = get_settings()
    os.makedirs(settings.model_path, exist_ok=True)

    print("[trainer] Collecting training data...")
    X, y = await _collect_training_data()
    print(f"[trainer] Total samples: {len(y)} | Class balance: {y.mean():.2%} BUY")

    print("[trainer] Training XGBoost model...")
    model, scaler, metrics = _train_xgboost(X, y)

    # Save model artifacts to disk
    model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_path  = os.path.join(settings.model_path, "xgb_model.pkl")
    scaler_path = os.path.join(settings.model_path, "scaler.pkl")

    with open(model_path, "wb")  as f: pickle.dump(model,  f)
    with open(scaler_path, "wb") as f: pickle.dump(scaler, f)

    print(f"[trainer] Model saved — accuracy: {metrics['accuracy']:.3f}, F1: {metrics['f1']:.3f}")

    # Hot-reload the model in the ModelManager (no restart needed)
    manager = ModelManager.get_instance()
    manager.load(model_path, scaler_path)

    # Store metrics in Supabase
    db = get_supabase()
    db.table("model_metrics").insert({
        "id":               str(uuid.uuid4()),
        "model_version":    model_version,
        "accuracy":         round(metrics["accuracy"], 4),
        "precision":        round(metrics["precision"], 4),
        "recall":           round(metrics["recall"], 4),
        "f1_score":         round(metrics["f1"], 4),
        "training_samples": int(metrics["training_samples"]),
        "trained_at":       datetime.now(timezone.utc).isoformat(),
    }).execute()

    return metrics
