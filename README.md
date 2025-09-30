🌟 HelixNet Platform: The Asynchronous Architecture

This repository contains the foundation for the HelixNet asynchronous web platform, utilizing FastAPI, Celery, and a full suite of containerized backend services for high-performance, real-world application development.
✅ CURRENT STATUS: TECHNICAL SPIKE COMPLETE (MVA)

The core infrastructure connection is verified and working. The local Python environment is successfully communicating with the Dockerized Postgres database.

    Endpoint Verified: GET /health returns 200 OK (Postgres connectivity confirmed).

    Database Verified: CRUD operations (POST/GET) on the /items endpoint successfully save and retrieve data from the helix_db database.

⚙️ Single Source of Truth: Environment Variables

All critical credentials and configuration settings are managed via the top-level .env file. These values are consistent across Docker services and local development.

Variable
	

Default Value
	

Purpose

POSTGRES_USER
	

helix_user
	

Database Login Username

POSTGRES_PASSWORD
	

helix_pass
	

Database Login Password

POSTGRES_DB
	

helix_db
	

Database Name

POSTGRES_HOST
	

postgres
	

Internal Host (used inside Docker containers)

REDIS_HOST
	

redis
	

Redis Cache/Celery Backend Host

RABBITMQ_HOST
	

rabbitmq
	

Celery Broker Host

MINIO_BUCKET
	

helixnet
	

S3 Object Storage Bucket Name

APP_PORT
	

8000
	

FastAPI Web/API Port
🏗️ Project Structure & Component Naming

We are moving away from the single isolated test file into a clean, scalable architecture. This structure ensures clean imports and separation of concerns.

Folder
	

Purpose
	

Key Files

app/db/
	

Database Core
	

database.py (Engine/Session/Dependencies), models.py (SQLAlchemy ORM definitions).

app/schemas/
	

Data Validation
	

item_schema.py, user_schema.py (Pydantic models for API request/response).

app/api/
	

FastAPI Routes
	

item_router.py, user_router.py (FastAPI APIRouter instances).

app/tasks/
	

Celery & Background
	

celery_app.py (Celery app setup), tasks.py (Task definitions), db_utils.py (Async DB helper for tasks).

app/
	

Application Entry
	

main.py (Initializes FastAPI, includes all routers, handles startup/shutdown events).
🚀 Service Access & Endpoints

Service
	

Port
	

Access URL
	

Tip for Login/Connection

Web (FastAPI)
	

8000
	

http://localhost:8000
	

Main application entry point.

FastAPI Docs
	

8000
	

http://localhost:8000/docs
	

Interactive Swagger UI.

Health Check
	

8000
	

http://localhost:8000/health
	

Confirms database connectivity.

RabbitMQ Admin
	

15672
	

http://localhost:15672
	

Use $RABBITMQ_USER and $RABBITMQ_PASS.

MinIO Console
	

9091
	

http://localhost:9091
	

Use $MINIO_ROOT_USER and $MINIO_ROOT_PASSWORD.

PGAdmin
	

5050
	

http://localhost:5050
	

Use $PGADMIN_DEFAULT_EMAIL and $PGADMIN_DEFAULT_PASSWORD.
🚧 Immediate Roadmap: Refactoring & Unit Verification

Our next steps are to move the code from the single testing file (app/api/services/check_api.py) into the final, clean structure, verifying the system health (/health endpoint) after each move.

Step
	

Focus
	

Action
	

Verification

R1
	

Database Core
	

Move engine, Base, and get_db_session logic into app/db/database.py.
	

RUN: uvicorn check_api:app --reload. TEST: GET /health must return 200 OK.

R2
	

ORM Models
	

Move the Item SQLAlchemy model into app/db/models.py.
	

RUN: uvicorn check_api:app --reload. TEST: GET /health must return 200 OK.

R3
	

Pydantic Schemas
	

Move the Item Pydantic models into app/schemas/item_schema.py.
	

RUN: uvicorn check_api:app --reload. TEST: GET /health must return 200 OK.

R4
	

API Router
	

Move all routes (/health, /items) into a new file: app/api/item_router.py and delete the testing file.
	

RUN: uvicorn app.main:app --reload (Finally using main.py). TEST: GET /health must return 200 OK.

HelixNet Core API

The Asynchronous Enterprise-Grade Backend for Scalable Job Processing.

This project utilizes a modern microservices-inspired architecture running on Docker Compose, integrating FastAPI, PostgreSQL, Celery, RabbitMQ, Redis, and MinIO.
🛠️ Development Setup Guide: The Vibe Coder's Ritual

The HelixNet environment is separated into two layers:

    The Infrastructure Layer (Docker): Contains all persistent services (Postgres, RabbitMQ, Redis, MinIO). These run in containers and communicate internally.

    The Application Layer (Local Venv): Contains the actual Python code (main.py, routers, services). We run this outside Docker during development so you can use features like Uvicorn's --reload and use a debugger, but it connects into the Docker network.

The Standard 3-Step Ritual to start local development (REQUIRED):
1. 🏗️ Create & Activate the Venv (The Local Toolbox)

This command creates and activates your isolated Python environment, ensuring you are using the correct dependencies and versions listed in requirements.txt.

# 1a. Create the venv (if it doesn't exist)
python3 -m venv venv

# 1b. Activate the venv (do this every time you start a new terminal session)
source venv/bin/activate
# You should see: (venv) angel@debian:~/repos/helixnet$

2. 📦 Install Dependencies (Fill the Toolbox)

This installs Uvicorn, FastAPI, SQLAlchemy, and all other necessary libraries into your new, active virtual environment.

(venv) angel@debian:~/repos/helixnet$ pip install -r requirements.txt

3. 🚀 Run the Infrastructure & API
A. Start the Backend Services (Docker Stack)

Ensure all essential services are running in the background.

docker compose up -d

B. Run the FastAPI Application (Local Development)

This starts your application, enables code reloading, and connects it to the live Docker services.

(venv) angel@debian:~/repos/helixnet$ uvicorn app.main:app --reload

🌐 Access & Monitoring UIs

Once the stack is running, you can access the core development tools:

Tool
	

Purpose
	

URL

Swagger UI
	

Interactive API documentation (Test endpoints here)
	

http://localhost:8000/docs

Health Check
	

Deep status check of all services (Postgres, Redis, RabbitMQ, MinIO)
	

http://localhost:8000/health

Celery Flower
	

Monitor Celery tasks and worker status
	

http://localhost:5555

RabbitMQ Mgmt
	

View queues and broker health
	

http://localhost:15672

MinIO Console
	

Object storage browser
	

http://localhost:9091

Post Enganglement Explained:
(venv) angel@debian:~/repos/helixnet$ uvicorn app.main:app --reload
INFO:     Will watch for changes in these directories: ['/home/angel/repos/helixnet']
ERROR:    [Errno 98] Address already in use
(venv) angel@debian:~/repos/helixnet$ 

HelixNet Core API
The Asynchronous Enterprise-Grade Backend for Scalable Job Processing.

This project utilizes a modern microservices-inspired architecture running on Docker Compose, integrating FastAPI, PostgreSQL, Celery, RabbitMQ, Redis, and MinIO.

🛠️ Development Setup Guide: 

The Vibe Coder's Ritual

The HelixNet environment is separated into two layers:

The Infrastructure Layer (Docker): 

Contains all persistent services (Postgres, RabbitMQ, Redis, MinIO). 
These run in containers and communicate internally.

The Application Layer (Local Venv): 
Contains the actual Python code (main.py, routers, services).
 We run this outside Docker during development so you can use features like Uvicorn's --reload and use a debugger, but it connects into the Docker network.
 
 The Standard 3-Step Ritual to start local development (REQUIRED):
 
 1. 🏗️ Create & Activate the Venv (The Local Toolbox)
 This command creates and activates your isolated Python environment, ensuring you are using the correct dependencies and versions listed in requirements.txt.
 # 1a. Create the venv (if it doesn't exist)
python3 -m venv venv

# 1b. Activate the venv (do this every time you start a new terminal session)
source venv/bin/activate
# You should see: (venv) angel@debian:~/repos/helixnet$

2. 📦 Install Dependencies (Fill the Toolbox)This installs Uvicorn, FastAPI, SQLAlchemy, and all other necessary libraries into your new, active virtual environment.

(venv) angel@debian:~/repos/helixnet$ pip install -r requirements.txt

3. 🚀 Run the Infrastructure & API

A. Start the Backend Services (Docker Stack)Ensure all essential services are running in the background.docker compose up -d

B. Run the FastAPI Application (Local Development)This starts your application, enables code reloading, and connects it to the live Docker services.

(venv) angel@debian:~/repos/helixnet$ uvicorn app.main:app --reload

C. Troubleshooting Port Conflicts (Address already in use)
If you get the [Errno 98] Address already in use error, it means port 8000 is already taken by another process (often a previous failed run or a running Docker container).

 Use these "secret instructions" to fix it:
 
 Find the Process ID (PID):# This command lists the process listening on port 8000

sudo lsof -i :8000

Identify the PID:

 Look in the output for the column labeled PID.
 
 Kill the Process: 
 
 Replace {PID} with the number you found.# This forcefully terminates the conflicting process

sudo kill -9 {PID}

Rerun the app: 
Go back to Step 3B and run uvicorn app.main:app --reload again.

🌐 Access & Monitoring UIs

Once the stack is running, you can access the core development tools:
Tool Purpose URL
Swagger UI  Interactive API documentation (Test endpoints here)
http://localhost:8000/docs

Health Check Deep status check of all services (Postgres, Redis, RabbitMQ, MinIO)
http://localhost:8000/health

Celery Flower Monitor Celery tasks and worker status 
http://localhost:5555

RabbitMQ MgmtView queues and broker health
http://localhost:15672

MinIO ConsoleObject storage browser
http://localhost:9091