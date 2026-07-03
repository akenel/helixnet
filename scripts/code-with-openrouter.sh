#!/usr/bin/env bash
# 🐺 Aider via OpenRouter — the reliable backup-brain backend (DeepSeek + many models).
# Usage: scripts/code-with-openrouter.sh [aider args]   |   MODEL=meta-llama/llama-3.3-70b-instruct scripts/code-with-openrouter.sh
set -a; source "$HOME/.aider-openrouter.env"; set +a
MODEL="${MODEL:-deepseek/deepseek-chat}"
exec "$HOME/.aider-venv/bin/aider" --model "openrouter/$MODEL" --no-show-model-warnings "$@"
