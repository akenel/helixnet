FROM python:3.11-slim

WORKDIR /app

# Copy the helix-pod files
COPY helix-pod/ /app/

# No dependencies needed - pure Python stdlib
EXPOSE 7791

CMD ["python3", "johnny-server.py", "--mode", "pollinations"]
