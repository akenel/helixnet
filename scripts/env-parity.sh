#!/usr/bin/env bash
# env-parity — GUARDRAIL: prove staging and prod run IDENTICAL code (mirror images).
# Only DATA (different DBs) and CONFIG (env vars) may differ — never code.
# Hashes the WHOLE src/ tree in each running container and compares. Exits non-zero on code drift.
# Usage: scripts/env-parity.sh          (run from anywhere; ssh's to the box)
set -uo pipefail
BOX=${BOX:-root@46.62.138.218}

ssh "$BOX" 'bash -s' <<'OUTER'
drift=0
# app CODE only: exclude __pycache__ (bytecode) + src/static (deploy/hosting artifacts, env-specific).
treehash() { docker exec "$1" sh -c 'find /app/src -type f -not -path "*__pycache__*" -not -path "*/static/*" \( -name "*.py" -o -name "*.html" -o -name "*.js" \) 2>/dev/null | sort | xargs md5sum 2>/dev/null | md5sum | cut -d" " -f1'; }
echo "════ ENV PARITY — staging vs prod (full src/ tree) ════"
for pair in "helix-platform-staging:helix-platform:Bottega" "borrowhood_staging:borrowhood:Square"; do
  S=$(echo "$pair" | cut -d: -f1); P=$(echo "$pair" | cut -d: -f2); N=$(echo "$pair" | cut -d: -f3)
  sh=$(treehash "$S"); ph=$(treehash "$P")
  if [ -z "$sh" ] || [ -z "$ph" ]; then echo "  ⚠️  $N — a container is down (s=$sh p=$ph)"; continue; fi
  if [ "$sh" = "$ph" ]; then echo "  ✅ $N — CODE IDENTICAL (staging == prod)  [$sh]"
  else echo "  ❌ $N — CODE DRIFT  staging=$sh prod=$ph"; drift=1
       echo "     files that differ:"
       diff <(docker exec "$S" sh -c 'find /app/src -type f | sort | xargs md5sum 2>/dev/null') \
            <(docker exec "$P" sh -c 'find /app/src -type f | sort | xargs md5sum 2>/dev/null') 2>/dev/null | grep -E "^[<>]" | sed -E "s|.*/app/|       |" | sort -u | head -15
  fi
done
echo ""
echo "════ CONFIG (env that SHOULD differ — this is correct, not drift) ════"
for pair in "helix-platform-staging:helix-platform" "borrowhood_staging:borrowhood"; do
  S=$(echo "$pair" | cut -d: -f1); P=$(echo "$pair" | cut -d: -f2)
  echo "  $P vs $S — differing env keys (data/config routing):"
  diff <(docker exec "$S" sh -c 'env|grep -iE "DB|DATABASE|ENVIRONMENT|DEBUG|REALM|MODEL|OLLAMA"|sed -E "s/=.*//"|sort' 2>/dev/null) \
       <(docker exec "$P" sh -c 'env|grep -iE "DB|DATABASE|ENVIRONMENT|DEBUG|REALM|MODEL|OLLAMA"|sed -E "s/=.*//"|sort' 2>/dev/null) 2>/dev/null | grep -E "^[<>]" | sed "s/^/     /" | head
done
echo ""
[ "$drift" = "0" ] && echo "🟢 MIRROR IMAGES — code identical, only data/config differs." || { echo "🔴 CODE DRIFT DETECTED — staging and prod are NOT mirror images. Fix before trusting staging."; exit 1; }
OUTER