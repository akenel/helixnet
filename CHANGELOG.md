# 🧩 HelixNet Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### 🚧 Work in Progress
- Setting up API orchestration layer (FastAPI)
- Preparing the message broker tuning (RabbitMQ + Redis)
- CI/CD automation for HelixNet stack

---

## [0.0.1] - 2025-11-10 🥋 *The Awakening*
### 🚀 Added
- Initial project structure and Dockerfile setup, fully refactored for clarity and speed ⚡  
- Modular Docker Compose stacks (`edge`, `auth`, `core`, `helix`) with clear separation of concerns 🧱  
- Keycloak identity provider wired to Traefik with mkcert TLS 🔐  
- Basic Celery worker integration with Redis message queue 🐇  
- DevContainer configuration for seamless VSCode remote development 🧠  
- `scripts/helix-status-v2.sh` for monitoring logs, health, and container orchestration 🧩  

### 🛠️ Changed
- Cleaned up redundant compose conditionals for modern Docker Compose 3.9 syntax  
- Unified `.env` handling for consistent developer and container environments  
- Simplified entrypoint scripts for easier debugging and traceability  

### ✅ Fixed
- Traefik TLS chain validation now passes mkcert self-signed checks  
- Docker socket permissions fixed for container-in-container builds 🧰  

### 🔒 Security
- Enforced `requirepass` for Redis local deployments  
- Isolated Keycloak and Traefik networks for reduced attack surface  

---

**Next Up:**
> 🧠 AI-assisted microservices, API gateway rate limiting, and async task pipelines.  
> Stay tuned for `v0.1.0 – The Orchestration Era`.

---

[Unreleased]: https://github.com/akenel/helixnet/compare/v0.0.1...HEAD  
[0.0.1]: https://github.com/akenel/helixnet/releases/tag/v0.0.1
