FROM python:3.11-slim

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     build-essential curl netcat && \
#     rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /code

# Install Python dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full repo
COPY . .

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
