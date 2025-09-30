# --- STAGE 1: Build Stage (Includes build tools) ---
FROM python:3.11-slim as builder

# Set environment to unbuffered to see logs immediately
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for asyncpg and psycopg2
# libpq-dev is essential for connecting to Postgres
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# --- STAGE 2: Final Runtime Stage (Smaller, cleaner image) ---
FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Copy the environment and Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code
# This copies everything from the root of your local repo into /code
COPY . /code/

# Default command (will be overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
