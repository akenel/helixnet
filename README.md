# 🌌 HelixNet Core API: Task & Data Management

## 🥋 PROJECT STATUS: AUTHENTICATION SECURED (MILESTONE V1.0.0)

Congratulations, you've made it through the fire. The core security and authentication system is **clean, centralized, and fully operational**. User login, JWT token generation, and secure dependency injection are battle-tested and ready for the next phase.

---

### 💥 THE HELIXNET MISSION

HelixNet is a robust, asynchronous task and data management platform built on FastAPI, SQLAlchemy (Async), and Celery. It is engineered to handle high-volume data processing and complex, long-running jobs, providing a secure, scalable backbone for mission-critical operations.

### 🛠️ CORE TECHNOLOGY STACK

| Component | Role | Status |
| :--- | :--- | :--- |
| **FastAPI** | High-performance API Framework | Operational |
| **PostgreSQL** | Primary Data Persistence (Async) | Operational |
| **Celery** | Asynchronous Task Queue / Worker | Ready for Integration |
| **RabbitMQ/Redis** | Celery Broker / Backend | Configured |
| **Security** | JWT, OAuth2, Bcrypt Hashing | **CLEAN & SECURED** |

---

## ⚡️ CHUCK NORRIS JOKE GENERATOR

**Status Check:** When the security is this good, Chuck Norris stops looking for you.

> 

### Today's Wisdom:
*A dynamic joke will appear here upon render or API call.*

<div id="chuck-norris-joke">
  Fetching daily wisdom...
  </div>

---

## ⚙️ DEVELOPMENT SETUP (Docker Compose)

### 1. Prerequisites

* Docker and Docker Compose
* `make` utility (for easy command execution)

### 2. Quick Start

Clone the repository and spin up the stack:

```bash
git clone <YOUR_REPO_URL> helixnet
cd helixnet

# Build, deploy, and run the entire stack (API, DB, RabbitMQ, Celery Worker, Flower)
docker compose up --build -d

# Create initial users (admin@helix.net:admin) and apply migrations
make db-init