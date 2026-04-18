"""
Background scheduler using APScheduler.
- Every hour:  generate forex signals for all pairs
- Every day at 02:00 UTC: retrain the ML model

All jobs are wrapped in broad exception handlers so a failure
in one job never crashes the uvicorn process.
"""
import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _run_async(coro):
    """Run an async coroutine in a fresh event loop (scheduler runs in a thread)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _job_generate_signals():
    try:
        from app.services.signal_service import generate_all_signals
        logger.info("[scheduler] Running signal generation job")
        signals = _run_async(generate_all_signals())
        logger.info(f"[scheduler] Generated {len(signals)} signals")
    except Exception as exc:
        # Log but never re-raise — a job failure must not crash uvicorn
        logger.error(f"[scheduler] Signal generation failed (non-fatal): {exc}")


def _job_retrain_model():
    try:
        from app.ml.trainer import train_and_save
        logger.info("[scheduler] Running daily model retrain")
        _run_async(train_and_save())
        logger.info("[scheduler] Model retrain completed")
    except Exception as exc:
        logger.error(f"[scheduler] Model retrain failed (non-fatal): {exc}")


def start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")

    # Hourly signal generation (at :00 of every hour)
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
    logger.info("[scheduler] Started — signals hourly, retrain daily at 02:00 UTC")

    # Defer the startup signal run by 10 s so the server finishes binding its port first
    # This prevents a slow API call from blocking the health-check window
    import threading
    def _deferred():
        import time
        time.sleep(10)
        _job_generate_signals()

    t = threading.Thread(target=_deferred, daemon=True)
    t.start()


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[scheduler] Stopped")
    
