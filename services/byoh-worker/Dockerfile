# BYOH render worker -- the "muscle" as a sidecar container.
# The app (helix-platform) has no Piper/ffmpeg; it POSTs text here and gets an MP4.
# This same image runs in staging/prod next to the app, or anywhere (BYOH).
FROM python:3.11-slim

# system deps: ffmpeg (media) + DejaVu font (captions)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg fonts-dejavu-core curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# python deps: the HTTP wire + Piper TTS
RUN pip install --no-cache-dir \
        fastapi "uvicorn[standard]" pydantic python-multipart httpx piper-tts

# the default voice ('en' = lessac-medium, fast + clean on CPU)
RUN mkdir -p /voices \
 && curl -sfL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" \
        -o /voices/en_US-lessac-medium.onnx \
 && curl -sfL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" \
        -o /voices/en_US-lessac-medium.onnx.json

WORKDIR /app
COPY render.py worker.py capabilities.py /app/

# container tool paths (render.py reads these env vars)
ENV PIPER_BIN=/usr/local/bin/piper \
    VOICES_DIR=/voices \
    FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf

EXPOSE 8800
CMD ["uvicorn", "worker:app", "--host", "0.0.0.0", "--port", "8800"]
