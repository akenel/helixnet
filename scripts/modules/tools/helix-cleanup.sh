#!/usr/bin/env bash
# Sherlock Prime-Time Cleanup (Bruce Lee Edition)
# ------------------------------------------------
# Safely restructures the compose/ directory into the new
# production-approved format:
#   helix-llm / helix-core / helix-main / auth / qdrant / traefik
# ------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
COMPOSE_DIR="$ROOT/compose"
ARCHIVE_DIR="$COMPOSE_DIR/_archive_legacy_$(date +%Y%m%d_%H%M%S)"

# Colors
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

echo -e "${CYAN}🔍 Sherlock Cleanup Initialized${NC}"
echo -e "${CYAN}Repo Root: ${ROOT}${NC}"
echo ""

# ---------------------------------------------------------
# step 1 — what we keep
# ---------------------------------------------------------
KEEP_DIRS=(
  "helix-llm"
  "helix-core"
  "helix-main"
  "qdrant"
  "traefik"
  "auth"
)

# step 2 — what gets archived if present
ARCHIVE_CANDIDATES=(
  "ollama"
  "gemini"
  "compose"
  "helix"
  "celery"
  "keycloak"
  "data"
  "config"
  "models"
  "cache"
  "postgres"
)

mkdir -p "$ARCHIVE_DIR"

echo -e "${CYAN}📦 Archive Directory: $ARCHIVE_DIR${NC}"
echo ""

echo -e "${CYAN}▶ Scanning compose/ ...${NC}"
sleep 1

for item in "$COMPOSE_DIR"/*; do
  name="$(basename "$item")"

  # skip archive dir itself.
  [[ "$name" == "_archive"* ]] && continue

  # keep dirs?
  if printf '%s\n' "${KEEP_DIRS[@]}" | grep -qx "$name"; then
    echo -e "   ${GREEN}✔ KEEPING:${NC} $name"
    continue
  fi

  # archive candidates
  if printf '%s\n' "${ARCHIVE_CANDIDATES[@]}" | grep -qx "$name"; then
    echo -e "   ${YELLOW}→ ARCHIVING:${NC} $name"
    mv "$COMPOSE_DIR/$name" "$ARCHIVE_DIR/"
    continue
  fi

  # unknown directory?
  echo -e "   ${RED}⚠ Unknown folder in compose/:${NC} $name"
  read -rp "      Archive it? (y/N): " ans
  if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
    mv "$COMPOSE_DIR/$name" "$ARCHIVE_DIR/"
  else
    echo "      Skipped."
  fi
done


# ---------------------------------------------------------
# step 3 — normalize core stack directories
# ---------------------------------------------------------

echo ""
echo -e "${CYAN}⛏ Ensuring final structure exists...${NC}"
mkdir -p "$COMPOSE_DIR/helix-llm"
mkdir -p "$COMPOSE_DIR/helix-core"
mkdir -p "$COMPOSE_DIR/helix-main"
mkdir -p "$COMPOSE_DIR/auth"
mkdir -p "$COMPOSE_DIR/qdrant"
mkdir -p "$COMPOSE_DIR/traefik"

echo -e "${GREEN}✔ Base structure ready${NC}"

# ---------------------------------------------------------
# step 4 — fix recursive compose/compose folders
# ---------------------------------------------------------

if [[ -d "$COMPOSE_DIR/compose" ]]; then
  echo -e "${YELLOW}⚠ Found recursive compose/compose — archiving it${NC}"
  mv "$COMPOSE_DIR/compose" "$ARCHIVE_DIR/compose_recursive"
fi

# ---------------------------------------------------------
# step 5 — detect ghost folders created by docker mounts
# ---------------------------------------------------------

echo ""
echo -e "${CYAN}👻 Searching for ghost folders (docker-created)...${NC}"

GHOSTS=$(find "$COMPOSE_DIR" -maxdepth 3 -type d -name "models" -o -name "cache" -o -name "data" -o -name "config" | grep -v "_archive")

if [[ -n "$GHOSTS" ]]; then
  echo "$GHOSTS" | while read -r g; do
    echo -e "${YELLOW}Ghost Dir:${NC} $g"
    read -rp "   Remove ghost? (y/N): " gx
    if [[ "$gx" == "y" ]]; then
      rm -rf "$g"
      echo -e "   ${GREEN}✔ removed${NC}"
    fi
  done
else
  echo -e "${GREEN}✔ No ghost folders detected${NC}"
fi

# ---------------------------------------------------------
# step 6 — validate final setup
# ---------------------------------------------------------

echo ""
echo -e "${CYAN}🧪 Final Structure:${NC}"

tree "$COMPOSE_DIR" || true

echo ""
echo -e "${GREEN}🎉 Cleanup complete!${NC}"
echo -e "${CYAN}Your repo is now Prime-Time Edition.${NC}"
