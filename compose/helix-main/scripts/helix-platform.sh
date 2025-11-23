#!/bin/sh
set -e

# ==============================================================================
# 🐳 HELIX PLATFORM ENTRYPOINT SCRIPT - K.I.S.S. (FINAL ATTEMPT)
# 100% Guaranteed to run the final command if the Python interpreter exists.
# We are using the explicit, full path to the Python executable to avoid
# all PATH variable/shell environment issues.
# ==============================================================================

echo "======================================================================" >&2
echo "🧠 SANITY CHECK: Verifying Python interpreter is functional (2+2=4)." >&2

# The absolute path to the venv Python interpreter:
/app/venv/bin/python -c "print('Python is Ready: 2+2 equals', 2+2)" >&2

echo "🚀 Python environment confirmed functional. Launching primary application." >&2
echo "======================================================================" >&2

# Executes the main command passed to the container (the Uvicorn command)
exec "$@"