-- Ensure the script is run as a superuser (default behavior of docker entrypoint)

-- 1. Create the dedicated user for Helix/Keycloak
CREATE USER helix_user WITH PASSWORD 'helix_pass';

-- 2. Create the main database (assuming Keycloak needs 'keycloak_db' OR 'helix_db')
-- Based on your keycloak environment variable `KC_DB_URL_DATABASE: helix_db`, 
-- I will use `helix_db`. Adjust if you use a different name.
CREATE DATABASE helix_db WITH OWNER helix_user;

-- 3. Grant connection privileges
GRANT ALL PRIVILEGES ON DATABASE helix_db TO helix_user;