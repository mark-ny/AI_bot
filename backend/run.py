import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")
print(f"sys.path[0]: {sys.path[0]}")
print("=" * 50)

required = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET"]
missing = [v for v in required if not os.environ.get(v)]
if missing:
    print("MISSING ENV VARS:", missing)
    print("Add them in Render Dashboard -> Environment tab")
    sys.exit(1)
print("ENV VARS: OK")

import importlib
for m in ["app","app.config","app.database","app.auth","app.models.schemas",
          "app.ml.features","app.ml.model_manager","app.services.data_service",
          "app.services.signal_service","app.services.scheduler",
          "app.routers.signals","app.routers.trades","app.routers.analytics",
          "app.routers.auth","app.routers.websocket","app.main"]:
    try:
        importlib.import_module(m)
        print(f"  OK: {m}")
    except Exception as e:
        print(f"  FAIL: {m} => {e}")
        sys.exit(1)

print("All imports OK - starting server...")
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
