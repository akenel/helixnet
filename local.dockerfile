# Local Dockerfile for Development
# This Dockerfile is used only during development and uses environment variables
# defined in your .env file for configuration.

# Use a specific Python base image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1 \
    # We choose a non-root user (1000) for better security, required by some PaaS providers
    # The cookiecutter often generates a custom user/group, but 1000/1000 is safer for general use.
    USER_UID=1000 \
    USER_GID=1000

# Create the application directory and set it as the working directory
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    # Clean up APT when done
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (from the local file)
COPY ./requirements/local.txt /app/requirements/local.txt
RUN pip install --no-cache-dir -r /app/requirements/local.txt

# Copy the rest of the application code
COPY . /app/

# Ensure the entrypoint script is executable
RUN chmod +x /app/entrypoint.sh
# The entrypoint script is typically created by cookiecutter-django to handle
# migrations, static files, and starting the gunicorn server in production, 
# or the runserver command in development.

# Optional: Set the non-root user (1000 is a standard user ID)
# USER 1000 

# The command to start the application (defined in docker-compose.yml)
# CMD ["/start"]
