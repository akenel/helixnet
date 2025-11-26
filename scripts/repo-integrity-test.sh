#!/bin/bash
set -eo pipefail

echo "--- Running Repository Integrity Checks ---"
FAILURES=0

# Check 1: Critical Files Existence
echo ""
echo "📁 Checking Required Files..."
REQUIRED_FILES=(
    "README.md"
    "env/helix.example.env"
    "Makefile"
    "compose/helix-core/core-stack.yml"
    "compose/helix-main/main-stack.yml"
    "src/main.py"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ FAILURE: Required file missing: $file"
        FAILURES=$((FAILURES + 1))
    else
        echo "✅ Found: $file"
    fi
done

# Check 2: .gitignore Integrity - Check for patterns (not exact matches)
echo ""
echo "🔒 Checking .gitignore Security Patterns..."
CRITICAL_PATTERNS=(
    ".env"
    "postgres-data"
    "models/"
    "*.pem"
    "*.key"
    "*.crt"
    "__pycache__"
)
MISSING_PATTERNS=""

for pattern in "${CRITICAL_PATTERNS[@]}"; do
    if ! grep -q "$pattern" .gitignore; then
        MISSING_PATTERNS+="  - ${pattern}\n"
        echo "❌ Missing pattern: $pattern"
    else
        echo "✅ Found pattern: $pattern"
    fi
done

if [ -n "$MISSING_PATTERNS" ]; then
    echo ""
    echo "⚠️  WARNING: Some critical patterns might be missing from .gitignore"
    # Don't fail on this - just warn
fi

# Check 3: Ensure no sensitive files are tracked
echo ""
echo "🛡️  Checking for Accidentally Tracked Sensitive Files..."
SENSITIVE_TRACKED=$(git ls-files | grep -E "\.env$|\.pem$|\.key$|\.crt$|postgres-data/|id_rsa|id_ed25519" | grep -v -E "\.example\.env$|\.env\.example$" || true)

if [ -n "$SENSITIVE_TRACKED" ]; then
    echo "❌ FAILURE: Sensitive files are being tracked in git:"
    echo "$SENSITIVE_TRACKED"
    FAILURES=$((FAILURES + 1))
else
    echo "✅ No sensitive files tracked in git"
fi

# Check 4: Docker Compose Files Exist and Have Basic YAML Structure
echo ""
echo "🐳 Checking Docker Compose Files..."
for compose_file in compose/*/*.yml; do
    if [ -f "$compose_file" ]; then
        # Just check if file is readable and has basic YAML structure
        # Note: We can't validate with 'docker compose config' because these files
        # depend on each other (multi-stack architecture)
        if grep -q "^services:" "$compose_file"; then
            echo "✅ Found: $compose_file"
        else
            echo "⚠️  Warning: $compose_file may have unusual structure"
        fi
    fi
done

# Final Summary
echo ""
echo "--- Test Summary ---"
if [ "$FAILURES" -eq 0 ]; then
    echo "✅ Repository Integrity Test PASSED! 🎉"
    exit 0
else
    echo "❌ Repository Integrity Test FAILED with $FAILURES issues. 🛑"
    exit 1
fi
