HelixNet Development Phase 5: Core Service and Data Flow
Goal

To transition HelixNet from an authenticated framework into a functioning asynchronous job processing and secure data management platform.
Phase 5 Focus Areas

1. Core Job Submission and Execution (Job Service)

This is where the application starts doing work. We need to expose endpoints for authenticated users to submit jobs and track their status.

Component
	

Description
	

Files Affected

Job Submission Endpoint
	

Expose a POST /jobs/ endpoint that accepts a user-defined job request (e.g., JobCreate schema).
	

routers/job_router.py

Task Dispatch Logic
	

The endpoint logic must hand off the job to the Celery worker immediately (fire-and-forget), returning a 202 Accepted status with the initial JobRead object.
	

services/job_service.py, tasks/job_tasks.py

Job Status Polling
	

Implement a GET /jobs/{job_id}/ endpoint to allow the client to monitor the job's progress (e.g., PENDING, RUNNING, SUCCESS, FAILURE).
	

routers/job_router.py, schemas/job_schema.py

Worker Implementation
	

Write the actual Celery task that processes the job logic, updates the database, and potentially generates artifacts.
	

tasks/job_tasks.py
2. Secure Artifact and Storage Management (MinIO Integration)

Jobs generate output (Artifacts) that must be stored securely (in MinIO/S3) and only accessible to authorized users.

Component
	

Description
	

Files Affected

Artifact Service
	

Core logic for interacting with MinIO: connecting, uploading, and downloading.
	

services/artifact_service.py

Secure Upload Logic
	

Implement a POST /artifacts/upload/ endpoint that returns a presigned URL. The client uses this URL to upload the file directly to MinIO, bypassing the application server.
	

routers/artifact_router.py

Secure Download Logic
	

Implement a GET /artifacts/{artifact_id}/download endpoint. This endpoint verifies user ownership/permissions and returns a short-lived presigned download URL for the client to retrieve the file.
	

routers/artifact_router.py

Model Linking
	

Ensure the Artifact model correctly stores the MinIO bucket, object name, and links back to the creating User and Job.
	

db/models/artifact_model.py
3. User Experience: Profile and Dashboard

The user needs a way to manage their new expanded profile data and see their activity.

Component
	

Description
	

Files Affected

User Profile Endpoint
	

Create a GET /users/me endpoint allowing the authenticated user to retrieve their full UserRead object, including the new fields (phone_number, web_url).
	

routers/user_router.py

Profile Update Endpoint
	

Implement a PUT /users/me endpoint, allowing the user to update fields like fullname, phone_number, and web_url using the UserUpdate schema.
	

routers/user_router.py, services/user_service.py

User Dashboard Template
	

Create the main front-end dashboard template (templates/dashboard.html or similar) where the user can view their submitted jobs and access their profile.
	

templates/dashboard.html

Job Listing
	

Implement the ability for the dashboard to call GET /jobs/ (filtered to the current user) to list all their past and pending jobs.
	

routers/job_router.py (enhancement)
Conclusion

Successfully executing this plan will move HelixNet past the foundational stage and establish the complete lifecycle of a job: Authentication → Job Submission → Asynchronous Processing (Worker) → Secure Data Storage (MinIO) → User Retrieval.

Start with Focus Area 1 (Core Job Service), as this proves the entire Celery/FastAPI/PostgreSQL flow is working end-to-end.
