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