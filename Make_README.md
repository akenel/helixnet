🥋 The HelixNet Makefile: Chuck's Combat Manual 🥋
Your Guide to Database Control and Code Deployment

Welcome, Warrior! This manual is your key to mastering the HelixNet development environment. We use make to abstract away the complexity of Docker Compose, database migrations (Alembic), and service restarts.

If you don't know which command to run, refer to the Routines section first. When in doubt, read the source code in the Makefile.
⚡ CORE WORKFLOW ROUTINES (The Iron Fists)

These are the 1-2 step processes that cover 99% of your daily operations.
Routine 1: Fresh Start / Debugging (The Nuclear Option) 💣

Purpose: Wipe everything, start from a guaranteed clean slate.
Use Case: You are setting up the project for the first time, or your database schema is corrupted.

Step
	

Command
	

Description

1. Annihilate
	

make reset-db
	

WARNING: This performs docker compose down -v (destroys volumes, which is where your database data lives). It rebuilds core services, builds app services, and applies all migrations.

2. Populate
	

make seed-data
	

Runs app/scripts/seed_users.py to populate default admin users.
Routine 2: Deploying New Code (The Quick Kick) ⬆️

Purpose: Update your running containers (helix-web-app, worker, beat) with new Python code.
Use Case: You changed logic in jobs.py, added a new API endpoint, or modified a service layer.

Step
	

Command
	

Description

1. Build & Deploy
	

make deploy-code
	

This is a composite command. It runs build-app (to include the new code) and then restarts all application containers to use the new image.
Routine 3: Changing the Database Schema (The Model Master) 🧬

Purpose: Add, remove, or modify SQLAlchemy models, and propagate those changes to the running database.
Use Case: You added a new table, changed a column name, or modified a column type.

Step
	

Command
	

Description

1. Define Change
	

make revision msg="A descriptive name"
	

Scans your Python models, compares them to the DB, and creates the migration script file in migrations/versions/. The msg option is MANDATORY!

2. Apply Change
	

make migrate
	

Applies all pending migrations (including the one you just created) to the database, bringing it to the latest schema head.
🛠️ COMMAND REFERENCE (The Tools of the Trade)
🗄️ Database & Migrations

Target
	

Description
	

Details & Options

migrate
	

🧬 Apply Alembic migrations to latest head
	

Runs alembic upgrade head inside the helix-web-app container. This is a safe, idempotent operation. Use this after running make revision.

revision
	

✍️ Create a new Alembic migration
	

Scans your Python models and compares them to the schema in the database. Requires the core-up services to be running. 
MANDATORY OPTION: make revision msg="add user profile table"

seed-data
	

🥕 Run the initial data seeding script
	

Executes python app/scripts/seed_users.py inside the web app container. Great for populating admin accounts or initial lookup data.

reset-db
	

💣 Reset database (WIPES VOLUMES!)
	

DANGER ZONE. Runs docker compose down -v to destroy data volumes, rebuilds core services (core-up), runs build-app, and then migrate. Use with extreme caution!
🚀 Application Lifecycle

These commands manage the running state of your Python application services (helix-web-app, worker, beat).

Target
	

Description
	

Details & Options

build-app
	

🏗️ Build application images
	

Executes docker compose ... build. This is the step that packages your latest Python code (including changes to jobs.py) into new Docker images. It does NOT restart the running containers.

deploy-code
	

⬆️ Build new code and restart services
	

The PRIMARY command for code changes. It depends on build-app and then runs docker compose up -d --remove-orphans to deploy the new images. This ensures your worker and beat containers load the latest logic.

restart-services
	

🔄 Quick restart for web app and workers
	

Runs docker compose restart helix-web-app worker beat. Use this only if you know your Docker images haven't changed (e.g., restarting just to clear memory or fix a quick race condition). If you changed Python code, use deploy-code.
⚙️ UNDERSTANDING THE PROFILES (The Context)

You'll notice commands use variables like $(CORE_PROFILES) and $(APP_PROFILES). This is how the system separates infrastructure from the application.

Variable
	

Services Included
	

Purpose

$(CORE_PROFILES)
	

postgres, redis, rabbitmq, traefik, pgadmin, etc.
	

Infrastructure services. These rarely need rebuilding. The core-up command manages these.

$(APP_PROFILES)
	

helix-web-app, worker, beat, flower
	

Application services. These contain your Python code. These are the focus of build-app and deploy-code.

May your builds be quick and your deployments flawless! 🥳