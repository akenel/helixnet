CREATE DATABASE keycloak_db
-- This script runs automatically when the Postgres container starts for the first time
-- (due to the volume mount in docker-compose.yml).
-- It creates the database and the specific user Keycloak needs.
-- 1. Create the dedicated Keycloak user using the credentials from .env
CREATE USER keycloak_db_user WITH PASSWORD 'admin';
-- 2. Create the Keycloak database and assign ownership to the new user
CREATE DATABASE keycloak_db WITH OWNER = keycloak_db_user ENCODING = 'UTF8';
-- 3. Grant connection privileges
GRANT ALL PRIVILEGES ON DATABASE keycloak_db TO keycloak_db_user;
-- #############################
-- # 🗃️ DATABASE CONFIGURATION (PostgreSQL)
-- ##############################
-- # ----------------------------------------------------------------
-- KEYCLOAK_DB_NAME=keycloak_db
-- KEYCLOAK_DB_PASS=admin
-- KEYCLOAK_DB_USER=admin