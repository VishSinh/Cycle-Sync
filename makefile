# Configuration Variables
COMPOSE_LOCAL := docker compose -f compose.local.yaml
COMPOSE_PROD := docker compose
PROJECT_NAME := myproject  # Replace with your project name

# Colors for terminal output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m  # No Color

# Default target
.DEFAULT_GOAL := help

# Mark all targets that don't represent files
.PHONY: help build-local build-prod run-local run-prod stop logs \
        migrations migrate-local migrate-prod shell-local shell-prod \
        clean prune test lint build-and-run-local build-and-run-prod

help:
	@echo "$(CYAN)Docker Development Commands:$(NC)"
	@echo "$(GREEN)make build-and-run-local$(NC) - Build and run local development environment"
	@echo "$(GREEN)make build-local$(NC)      - Build local development containers"
	@echo "$(GREEN)make run-local$(NC)        - Run local development server"
	@echo "$(GREEN)make migrations$(NC)       - Create new database migrations"
	@echo "$(GREEN)make migrate-local$(NC)    - Apply migrations locally"
	@echo "$(GREEN)make shell-local$(NC)      - Open Python shell locally"
	@echo "$(CYAN)Docker Production Commands:$(NC)"
	@echo "$(GREEN)make build-and-run-prod$(NC) - Build and run production environment"
	@echo "$(GREEN)make build-prod$(NC)       - Build production containers"
	@echo "$(GREEN)make run-prod$(NC)         - Run production server"
	@echo "$(GREEN)make migrate-prod$(NC)     - Apply migrations in production"
	@echo "$(GREEN)make shell-prod$(NC)       - Open Python shell in production"
	@echo "$(CYAN)Utility Commands:$(NC)"
	@echo "$(GREEN)make stop$(NC)             - Stop all running containers"
	@echo "$(GREEN)make logs$(NC)             - View container logs"
	@echo "$(GREEN)make clean$(NC)            - Remove containers and volumes"
	@echo "$(GREEN)make prune$(NC)            - Deep clean Docker system"
	@echo "$(GREEN)make test$(NC)             - Run tests"
	@echo "$(GREEN)make lint$(NC)             - Run code linting"

# Combined build and run commands
build-and-run-local:
	@echo "$(YELLOW)Building and running local environment...$(NC)"
	$(COMPOSE_LOCAL) build --pull
	$(COMPOSE_LOCAL) run --rm web python manage.py makemigrations
	$(COMPOSE_LOCAL) run --rm web python manage.py migrate
	$(COMPOSE_LOCAL) up

build-and-run-prod:
	@echo "$(YELLOW)Building and running production environment...$(NC)"
	$(COMPOSE_PROD) build --pull
	$(COMPOSE_PROD) run --rm web python manage.py migrate
	$(COMPOSE_PROD) up -d

# Development commands
build-local:
	@echo "$(YELLOW)Building local containers...$(NC)"
	$(COMPOSE_LOCAL) build --pull --no-cache

run-local: migrate-local
	@echo "$(YELLOW)Starting local development server...$(NC)"
	$(COMPOSE_LOCAL) up

migrations:
	@echo "$(YELLOW)Creating new migrations...$(NC)"
	$(COMPOSE_LOCAL) run --rm web python manage.py makemigrations

migrate-local:
	@echo "$(YELLOW)Applying migrations locally...$(NC)"
	$(COMPOSE_LOCAL) run --rm web python manage.py migrate

shell-local:
	@echo "$(YELLOW)Opening Python shell locally...$(NC)"
	$(COMPOSE_LOCAL) run --rm web python manage.py shell

# Production commands
build-prod:
	@echo "$(YELLOW)Building production containers...$(NC)"
	$(COMPOSE_PROD) build --pull --no-cache

run-prod: migrate-prod
	@echo "$(YELLOW)Starting production server...$(NC)"
	$(COMPOSE_PROD) up -d

migrate-prod:
	@echo "$(YELLOW)Applying migrations in production...$(NC)"
	$(COMPOSE_PROD) run --rm web python manage.py migrate

shell-prod:
	@echo "$(YELLOW)Opening Python shell in production...$(NC)"
	$(COMPOSE_PROD) run --rm web python manage.py shell

# Utility commands
stop:
	@echo "$(YELLOW)Stopping all containers...$(NC)"
	$(COMPOSE_LOCAL) down
	$(COMPOSE_PROD) down

logs:
	@echo "$(YELLOW)Viewing container logs...$(NC)"
	$(COMPOSE_PROD) logs -f

clean:
	@echo "$(RED)Removing containers and volumes...$(NC)"
	$(COMPOSE_LOCAL) down -v --remove-orphans
	$(COMPOSE_PROD) down -v --remove-orphans

prune:
	@echo "$(RED)Deep cleaning Docker system...$(NC)"
	docker system prune -af

test:
	@echo "$(YELLOW)Running tests...$(NC)"
	$(COMPOSE_LOCAL) run --rm web python manage.py test

lint:
	@echo "$(YELLOW)Running code linting...$(NC)"
	$(COMPOSE_LOCAL) run --rm web flake8