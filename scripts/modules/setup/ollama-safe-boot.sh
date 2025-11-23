#!/usr/bin/env bash

echo "🧠 Configuring Ollama safe mode..."

# Remove all large models
ollama list | grep -v "tiny\|mini\|small" | awk '{print $1}' | while read -r m; do
    echo "❌ Removing heavy model: $m"
    ollama rm "$m"
done

echo "✔ Installing CPU-friendly models..."
ollama pull phi3:mini
ollama pull llama3.2:1b
ollama pull tinydolphin
