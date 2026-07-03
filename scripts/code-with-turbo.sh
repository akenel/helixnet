#!/usr/bin/env bash
# 🐺 Code with YOUR Ollama Turbo (the backup-brain parachute). DeepSeek/qwen3-coder etc. drive Aider.
# Usage:   scripts/code-with-turbo.sh                 # interactive, deepseek-v3.2
#          MODEL=qwen3-coder:480b scripts/code-with-turbo.sh
#          scripts/code-with-turbo.sh --message "add X" path/to/file.py   # one-shot
set -a; source "$HOME/.aider-turbo.env"; set +a
MODEL="${MODEL:-deepseek-v3.2}"
exec "$HOME/.aider-venv/bin/aider" --model "openai/$MODEL" --no-show-model-warnings "$@"
