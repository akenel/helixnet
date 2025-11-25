#!/bin/bash
set -eo pipefail

echo "--- Running Repository Integrity Checks ---"
FAILURES=0

# Check 1: Critical Files Existence
REQUIRED_FILES=("docker-compose.yml" "README.md" ".env.example")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ FAILURE: Required file missing: $file"
        FAILURES=$((FAILURES + 1))
    else
        echo "✅ Found: $file"
    fi
done

# Check 2: .gitignore Integrity (Reusing the logic from the GH Action)
CRITICAL_IGNORES=(".env" "postgres-data/" "models/" "*.pem" "*.key")
MISSING_PATTERNS=""

for pattern in "${CRITICAL_IGNORES[@]}"; do
    if ! grep -q "^${pattern}\$" .gitignore; then
        MISSING_PATTERNS+="${pattern}\n"
    fi
done

if [ -n "$MISSING_PATTERNS" ]; then
    echo "❌ FAILURE: Critical patterns missing from .gitignore:"
    echo -e "$MISSING_PATTERNS"
    FAILURES=$((FAILURES + 1))
else
    echo "✅ .gitignore integrity check passed."
fi

# Final Summary
echo "--- Test Summary ---"
if [ "$FAILURES" -eq 0 ]; then
    echo "Repository Integrity Test PASSED! 🎉"
else
    echo "Repository Integrity Test FAILED with $FAILURES issues. 🛑"
    exit 1
fi