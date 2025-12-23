FROM python:3.11-slim

WORKDIR /app

# Install dependencies for art_providers and TTS
RUN pip install --no-cache-dir pyyaml edge-tts

# Copy the helix-pod files
COPY helix-pod/ /app/

EXPOSE 7791

CMD ["python3", "johnny-server.py", "--mode", "pollinations"]
