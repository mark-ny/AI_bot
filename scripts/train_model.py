#!/usr/bin/env python3
"""
Manual model training script.
Run: python scripts/train_model.py
Useful for initial model training before first deploy.
"""
import asyncio
import sys
import os

# Add backend to path so imports work from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.ml.trainer import train_and_save


async def main():
    print("=" * 50)
    print("ForexAI — Manual Model Training")
    print("=" * 50)
    metrics = await train_and_save()
    print("\n✅ Training complete!")
    print(f"   Accuracy:  {metrics['accuracy']:.3f}")
    print(f"   Precision: {metrics['precision']:.3f}")
    print(f"   Recall:    {metrics['recall']:.3f}")
    print(f"   F1 Score:  {metrics['f1']:.3f}")
    print(f"   Samples:   {int(metrics['training_samples'])}")


if __name__ == "__main__":
    asyncio.run(main())
