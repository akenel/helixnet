CREATE ROLE helix_user WITH LOGIN PASSWORD 'helix_pass';
CREATE DATABASE helix_db OWNER helix_user;
GRANT ALL PRIVILEGES ON DATABASE helix_db TO helix_user;

