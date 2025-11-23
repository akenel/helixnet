# in TUI: when user chooses a model from helix-ollama.sh list, write to file
selected_model="tinyllama:latest"
echo "$selected_model" > /var/tmp/helix_ollama_model
# update worker env (if running inside Docker you can restart debllm service or set env via docker)
docker restart debllm
