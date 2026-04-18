import sys, os

# Force unbuffered output — critical for Render log capture
os.environ["PYTHONUNBUFFERED"] = "1"

def p(msg):
    # Write to BOTH stderr (never buffered) and stdout
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

p("==================================================")
p("FOREXAI STARTUP")
p(f"Python: {sys.version}")
p(f"CWD: {os.getcwd()}")
p("==================================================")

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
p(f"sys.path[0] = {backend_dir}")

# Check env vars
required = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET"]
missing = [v for v in required if not os.environ.get(v)]
if missing:
    for v in missing:
        p(f"MISSING ENV VAR: {v}")
    p("Fix: Render Dashboard -> Environment tab -> add missing vars -> redeploy")
    sys.exit(1)
p("ENV VARS: all present")

# Test imports one by one
import importlib
modules = [
    "app",
    "app.config",
    "app.database",
    "app.auth",
    "app.models",
    "app.models.schemas",
    "app.ml",
    "app.ml.features",
    "app.ml.model_manager",
    "app.services",
    "app.services.data_service",
    "app.services.signal_service",
    "app.services.scheduler",
    "app.routers",
    "app.routers.signals",
    "app.routers.trades",
    "app.routers.analytics",
    "app.routers.auth",
    "app.routers.websocket",
    "app.main",
]

for m in modules:
    try:
        importlib.import_module(m)
        p(f"OK: {m}")
    except Exception as e:
        p(f"FAIL: {m}")
        p(f"  Error type: {type(e).__name__}")
        p(f"  Error msg:  {e}")
        import traceback
        p(traceback.format_exc())
        sys.exit(1)

p("All imports OK — launching uvicorn")
import uvicorn
port = int(os.environ.get("PORT", 8000))
uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
