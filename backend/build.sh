#!/usr/bin/env bash
set -e

echo "=== Python version check ==="
python --version
PYVER=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python: $PYVER"

if [ "$PYVER" != "3.11" ] && [ "$PYVER" != "3.12" ] && [ "$PYVER" != "3.10" ]; then
  echo ""
  echo "ERROR: Unsupported Python version $PYVER"
  echo "pandas/numpy/xgboost do NOT have wheels for Python $PYVER yet."
  echo ""
  echo "Fix: In Render Dashboard → Environment tab, add:"
  echo "  PYTHON_VERSION = 3.11.9"
  echo ""
  echo "Then redeploy."
  exit 1
fi

echo "=== Installing packages (binary wheels only) ==="
pip install --upgrade pip

# Install scientific stack first, binary-only — fail fast if no wheel exists
pip install \
  --only-binary=numpy,pandas,scikit-learn,xgboost \
  numpy==1.26.4 \
  pandas==2.2.2 \
  scikit-learn==1.4.2 \
  xgboost==2.0.3

# Install rest of dependencies
pip install -r requirements.txt

echo "=== Build complete ==="
