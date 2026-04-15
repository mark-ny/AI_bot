"""
Background scheduler using APScheduler.
- Every hour:  generate forex signals for all pairs
- Every day at 02:00 UTC: retrain the ML model
"""
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler: BackgroundScheduler | None = None


def _run_async(coro):
    """Helper to run async functions in the sync scheduler thread."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _job_generate_signals():
    from app.services.signal_service import generate_all_signals
    print("[scheduler] Running signal generation job")
    try:
        signals = _run_async(generate_all_signals())
        print(f"[scheduler] Generated {len(signals)} signals")
    except Exception as exc:
        print(f"[scheduler] Signal generation failed: {exc}")


def _job_retrain_model():
    from app.ml.trainer import train_and_save
    print("[scheduler] Running daily model retrain")
    try:
        _run_async(train_and_save())
        print("[scheduler] Model retrain completed")
    except Exception as exc:
        print(f"[scheduler] Model retrain failed: {exc}")


def start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")

    # Hourly signal generation (at minute 0)
    _scheduler.add_job(
        _job_generate_signals,
        CronTrigger(minute=0),
        id="generate_signals",
        replace_existing=True,
    )

    # Daily retrain at 02:00 UTC
    _scheduler.add_job(
        _job_retrain_model,
        CronTrigger(hour=2, minute=0),
        id="retrain_model",
        replace_existing=True,
    )

    _scheduler.start()
    print("[scheduler] Started — signals hourly, retrain daily at 02:00 UTC")

    # Run signal generation once on startup
    _job_generate_signals()


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[scheduler] Stopped")
