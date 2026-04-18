import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOG = []
def p(msg):
    print(msg, flush=True)
    LOG.append(msg)

p("=" * 50)
p(f"Python: {sys.version}")
p(f"CWD: {os.getcwd()}")
p(f"sys.path[0]: {sys.path[0]}")
p("=" * 50)

required = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET"]
missing = [v for v in required if not os.environ.get(v)]
if missing:
    p("MISSING ENV VARS: " + str(missing))
    p("Go to Render Dashboard -> Environment tab -> add these -> redeploy")
    sys.exit(1)
p("ENV VARS: all present OK")

import importlib
modules = [
    "app", "app.config", "app.database", "app.auth",
    "app.models.schemas", "app.ml.features", "app.ml.model_manager",
    "app.services.data_service", "app.services.signal_service",
    "app.services.scheduler", "app.routers.signals",
    "app.routers.trades", "app.routers.analytics",
    "app.routers.auth", "app.routers.websocket", "app.main"
]
failed = False
for m in modules:
    try:
        importlib.import_module(m)
        p(f"  OK: {m}")
    except Exception as e:
        p(f"  FAIL: {m} => {type(e).__name__}: {e}")
        failed = True
        break

if failed:
    sys.exit(1)

p("All imports OK - starting uvicorn...")
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
