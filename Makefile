# Makefile

# Variables for Docker Compose commands
COMPOSE_FILE := docker-compose.yaml

# Define profiles for easy launch control
CORE_SERVICES := postgres redis rabbitmq minio
APP_SERVICES := web worker

# Default target for quick start
.PHONY: start
start: ## Launches core infrastructure and the application services.
	docker compose -f $(COMPOSE_FILE) --profile core --profile app up -d

.PHONY: core-up
core-up: ## Launches only the core infrastructure (DBs, Cache, Broker)
	docker compose -f $(COMPOSE_FILE) --profile core up -d

.PHONY: stop
stop: ## Stops and removes all HelixNet containers and default network.
	docker compose -f $(COMPOSE_FILE) down

.PHONY: build
build: ## Builds the application Docker image.
	docker compose -f $(COMPOSE_FILE) build

.PHONY: logs
logs: ## Follows the logs for all running services.
	docker compose -f $(COMPOSE_FILE) logs -f

.PHONY: links
links: ## Displays essential access links.
	@echo "\n--- HelixNet Access Links ---"
	@echo "Web App:      http://localhost:8000"
	@echo "MinIO Console:  http://localhost:9001 (User/Pass from .env)"
	@echo "RabbitMQ Mgmt:  http://localhost:15672 (User/Pass from .env)"
	@echo "---------------------------\n"

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'