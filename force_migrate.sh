#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting forced Alembic migration ==="

# Ensure project root is in PYTHONPATH
export PYTHONPATH="/code:$PYTHONPATH"

echo "--- Attempt #1: Run Alembic via Python API ---"
python - <<'PYCODE'
import sys
try:
    from alembic.config import main
    import os

    if "/code" not in sys.path:
        sys.path.append("/code")

    sys.argv = ["alembic", "upgrade", "head"]

    print("Alembic core function imported. Executing migration...")
    main()
    print("----------------------------------------------------------------")
    print("SUCCESS: Database migration complete!")

except ModuleNotFoundError as e:
    print(f"FAILURE: Cannot import Alembic module: {e}")
    sys.exit(99)  # special exit code for fallback

except Exception as e:
    print(f"FAILURE: Migration failed: {e}")
    sys.exit(1)
PYCODE

# Capture exit code
RESULT=$?

if [ "$RESULT" -eq 99 ]; then
    echo "--- Attempt #2: Fallback to Alembic CLI ---"
    /usr/local/bin/alembic -c /code/alembic.ini upgrade head
    echo "----------------------------------------------------------------"
    echo "SUCCESS: Fallback migration complete!"
elif [ "$RESULT" -ne 0 ]; then
    echo "FINAL FAILURE: Migration could not be completed."
    exit 1
fi

echo "=== Migration process finished ==="
