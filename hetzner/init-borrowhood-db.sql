-- Create BorrowHood database and user in shared Postgres
-- Run once: docker exec -i postgres psql -U helix_user -d helix_db < init-borrowhood-db.sql

CREATE USER borrowhood WITH PASSWORD 'borrowhood_pass';
CREATE DATABASE borrowhood OWNER borrowhood;
GRANT ALL PRIVILEGES ON DATABASE borrowhood TO borrowhood;
