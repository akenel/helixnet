# 🌌 HelixNet Core API: Task & Data Management

This repository contains the core services for HelixNet, designed for high-volume data processing and task management using FastAPI, PostgreSQL, RabbitMQ/Celery, and Redis, all orchestrated via Docker Compose and secured with Traefik.

## 🚀 Deployment & Access

The entire application stack is containerized using Docker Compose. Access to all web services is managed via **Traefik**, utilizing HTTPS and custom hostnames defined in your local `/etc/hosts` file.

### Prerequisites

1.  **Docker & Docker Compose:** Must be installed and running.
2.  **Hostnames:** You must add the following entries to your local machine's `/etc/hosts` file, mapping them to your Traefik entry point (usually the IP address of the machine running Docker, or `127.0.0.1`):

    ```
    127.0.0.1  helix.local
    127.0.0.1  flower.helix.local
    127.0.0.1  pgadmin.helix.local
    # ... any other Traefik-routed services
    ```

### Access Points

Once the stack is running via `docker-compose up -d`, services are available via HTTPS:

| Service | Access URL | Purpose |
| :--- | :--- | :--- |
| **Core API (FastAPI)** | `https://helix.local/` | Main application endpoint. |
| **Swagger Docs** | `https://helix.local/docs` | Interactive API documentation. |
| **Flower Dashboard** | `https://flower.helix.local/` | Celery task monitoring and worker management. |
| **PGAdmin** | `https://pgadmin.helix.local/` | PostgreSQL database administration GUI. |

### Database Setup

To prepare the database and seed initial users (required before API testing):

1.  Start the services: `docker-compose up -d`
2.  Run the setup command: `make setup` (This executes migrations and seeding).

---

🌌 HelixNet Core API: Task & Data Management
🛠️ Overview

This is the core service for high-volume data processing and user management, built with FastAPI, PostgreSQL, and Celery for asynchronous job handling.

This API adheres to the standard versioning prefix /api/v1 for all application routes (Authentication, Users, Jobs), with the exception of the system health check.
🚀 Getting Started

The API is fully self-documenting. Once the server is running, you can access the interactive Swagger UI documentation here:

    API Docs (Swagger UI): [Your Host]/docs

    OpenAPI Specification: [Your Host]/openapi.json

🔐 Authentication (OAuth2)

All protected routes require a Bearer Token obtained via the OAuth2 Password flow.
1. Get an Access Token

Endpoint
	

Method
	

Description

/api/v1/token
	

POST
	

Exchange username (email) and password for a JWT Access Token.

Request Example (using curl):

curl -X POST \
  "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=marcel@helix.net&password=yourpassword"

2. Use the Token

Use the returned access_token in the Authorization header of all subsequent requests:
Authorization: Bearer <YOUR_ACCESS_TOKEN>
👤 User Management (/api/v1/)

The User endpoints handle standard CRUD operations and require an active Bearer Token.

Path
	

Method
	

Description
	

Requires Auth

/api/v1/
	

POST
	

Create User: Register a new user account.
	

❌ No

/api/v1/
	

GET
	

Read Users: Retrieve a paginated list of all active users.
	

✅ Yes

/api/v1/me
	

GET
	

Get Current User Profile: Retrieve the profile of the authenticated user.
	

✅ Yes

/api/v1/{user_id}
	

GET
	

Read User: Retrieve a specific user by their UUID.
	

✅ Yes

/api/v1/{user_id}
	

PATCH
	

Update User: Modify a user's details (email, password, etc.).
	

✅ Yes

/api/v1/{user_id}
	

DELETE
	

Delete User: Soft-delete a user account.
	

✅ Yes
🎯 Asynchronous Job Processing (/api/v1/ & /api/v1/{job_id})

Heavy lifting tasks are offloaded to a dedicated Celery worker and tracked persistently in PostgreSQL.

Path
	

Method
	

Description
	

Status Code

/api/v1/
	

POST
	

Submit New Job: Submits a JobSubmission payload to the worker queue.
	

202 Accepted

/api/v1/{job_id}
	

GET
	

Retrieve Job Status: Check the status and fetch the final result_data upon success.
	

200 OK

Job Statuses:

    PENDING/STARTED: Job is queued or actively running.

    SUCCESS: Job is complete. The result will be in result_data.

    FAILURE: Job failed. Error details will be in the message field.

💖 System Health Check

This endpoint performs deep checks on critical dependencies, including PostgreSQL and Celery.

Endpoint
	

Method
	

Description
	

Success
	

Failure

/health/
	

GET
	

Checks connectivity and readiness of the DB and background worker.
	

200 OK (All services up)
	

503 Service Unavailable