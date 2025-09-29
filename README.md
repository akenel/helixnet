HelixNet Platform

This repository contains the setup for the HelixNet asynchronous web platform, utilizing FastAPI, Celery, and a full suite of containerized backend services for modern application development.
🚀 Getting Started

This project relies entirely on Docker and Docker Compose for a consistent environment.
Prerequisites

    Docker

    make (optional, but highly recommended for command shortcuts)

Startup

The recommended way to start the entire stack is using the provided Makefile commands.

    Stop any existing containers and clean up:

    make stop

    Build the application image:
    (This step is crucial after changing Python dependencies or the Dockerfile.)

    make build

    Launch all services:
    (Since all services now use the core profile, this starts everything.)

    make start
    # Equivalent to: docker compose up -d --profile core

    View Logs:
    (Keep this running to monitor startup status.)

    make logs

Accessing Services

Service
	

Port
	

Description

Web App (FastAPI)
	

http://localhost:8000
	

Main application entry point.

RabbitMQ Management
	

http://localhost:15672
	

Broker management dashboard.

MinIO Console (S3)
	

http://localhost:9001
	

Object storage console.
🏗️ Project Structure

The structure is set up for a Python package (app/) that is flattened inside the Docker container's working directory (/app) for clean imports.

.
├── app/
│   ├── main.py        # FastAPI entrypoint
│   ├── routes/        # API endpoints
│   ├── tasks/         # Celery tasks definition and worker setup
│   ├── static/        # Static assets
│   └── templates/     # Jinja2 templates
├── docker-compose.yaml # Defines all 8 services
├── Dockerfile          # Builds the web/worker images
└── requirements.txt    # Python dependencies

⚙️ Key Configuration Notes

The stability of this setup relies on a few critical configuration points:

    Clean Container Paths: We explicitly copy the contents of the local app/ folder into the container's working directory (/app) using COPY app/ /app/ in the Dockerfile. This avoids the problematic app.app nested package name.

    Local Development Volumes: To ensure real-time code updates and to bypass lingering Python import issues during development, the docker-compose.yaml uses volume mounts for the application containers:

    volumes:
      - ./app:/app

    This guarantees that the container always finds the correct main.py and the tasks package, resolving the persistent ModuleNotFoundError issues we previously encountered.

    Celery Command: The worker command uses the simplified import path, which works correctly thanks to the volume mount:

    command: python -m celery -A tasks.celery_app worker --loglevel=info

ROADMAP:

Step	Component	Focus	Why	Priority
1	Setup & Core Files	requirements.txt, config.yaml (Base), .env (Secrets), Project Structure.	Establishes all dependencies and configuration.	P1: Immediate
2	Container Infrastructure	docker-compose.yaml (Core Services Profile: Postgres, Redis, RabbitMQ, MinIO).	Spins up all necessary infrastructure components.	P1: Immediate
3	Data Persistence & Storage	Postgres and MinIO setup, initial health checks.	Ensures data integrity and artifact storage.	P1: Immediate
4	FastAPI Service	Dockerfile for Python app, app/main.py entry point, basic health check endpoint.	The user-facing application layer.	P2: Critical Dev
5	Celery Service	Dockerfile for Celery worker, celeryconfig.py, task registration.	The asynchronous job processing layer.	P2: Critical Dev
6	Network & Initial Test	Service networking verification, first Hello World task via the FastAPI endpoint to Celery.	Validates the entire distributed system chain.	P3: Verification

URLs 
Service	Host Port	Access URL	Purpose	Login/Credentials
Web (FastAPI)	8000	http://localhost:8000	Main application endpoint	N/A
Web Health Check	8000	http://localhost:8000/health	Confirm application is running	N/A
MinIO Console	9091	http://localhost:9091	Object Storage Web UI	Use $MINIO_ROOT_USER and $MINIO_ROOT_PASSWORD
MinIO API	9090	http://localhost:9090	API access endpoint	N/A (Tested for reachability)
RabbitMQ Admin	15672	http://localhost:15672	Message Broker Management UI	Use $RABBITMQ_USER and $RABBITMQ_PASS
Postgres	(Internal)	N/A	Database access (Internal)	Use $POSTGRES_USER and $POSTGRES_PASSWORD
Redis	6379	N/A	Caching/Results backend	N/A (Internal use only)