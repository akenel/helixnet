FROM python:3.11-slim

WORKDIR /app

# Install dependencies for art_providers
RUN pip install --no-cache-dir pyyaml

# Copy the helix-pod files
COPY helix-pod/ /app/

EXPOSE 7791

CMD ["python3", "johnny-server.py", "--mode", "pollinations"]
