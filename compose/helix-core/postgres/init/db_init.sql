CREATE DATABASE keycloak_db
-- This script runs automatically when the Postgres container starts for the first time
-- (due to the volume mount in docker-compose.yml).
-- It creates the database and the specific user Keycloak needs.
-- 1. Create the dedicated Keycloak user using the credentials from .env
CREATE USER helix_user WITH PASSWORD 'helix_pass';
-- 2. Create the Keycloak database and assign ownership to the new user
CREATE DATABASE helix_db WITH OWNER = helix_user ENCODING = 'UTF8';
-- 3. Grant connection privileges
GRANT ALL PRIVILEGES ON DATABASE helix_db TO helix_user;
-- #############################
-- # 🗃️ DATABASE CONFIGURATION (PostgreSQL)
-- ##############################
-- # ----------------------------------------------------------------
-- KEYCLOAK_DB_NAME=helix_db   
-- KEYCLOAK_DB_PASS=helix_pass
-- KEYCLOAK_DB_USER=helix_user
-- # ----------------------------------------------------------------
-- # ----------------------------------------------------------------
-- HX_SUPER_EMAIL=super@helix.net
-- HX_SUPER_PASS=helix_pass
-- HX_SUPER_USER=helix_user
-- # ----------------------------------------------------------------
