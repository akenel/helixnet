# --- STAGE 1: Build Stage (Includes build tools) ---
FROM python:3.11-slim AS builder

# Set environment to unbuffered to see logs immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl docker.io build-essential libpq-dev gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: Runtime / Dev Stage ---
FROM python:3.11-slim AS final

# Working directory inside container
WORKDIR /code

# 🧠 Allow build-time selection of environment
ARG ENVIRONMENT=dev
ENV ENVIRONMENT=${ENVIRONMENT}

# Install only minimal runtime deps by default
# Install dev tools *only if ENVIRONMENT=dev or uat*
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl jq && \
    if [ "$ENVIRONMENT" = "dev" ] || [ "$ENVIRONMENT" = "uat" ]; then \
    apt-get install -y --no-install-recommends make vim-tiny git docker.io; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# Copy Python deps from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy codebase
COPY . /code/

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default startup command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]