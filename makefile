# Configuration Variables
COMPOSE := docker compose
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
.PHONY: help build run stop logs migrations migrate shell clean prune test lint build-and-run

help:
	@echo "$(CYAN)Docker Development Commands:$(NC)"
	@echo "$(GREEN)make build-and-run$(NC)    - Build and run the environment"
	@echo "$(GREEN)make build$(NC)            - Build Docker containers"
	@echo "$(GREEN)make run$(NC)              - Run the server"
	@echo "$(GREEN)make migrations$(NC)       - Create new database migrations"
	@echo "$(GREEN)make migrate$(NC)          - Apply database migrations"
	@echo "$(GREEN)make shell$(NC)            - Open Python shell"
	@echo "$(CYAN)Utility Commands:$(NC)"
	@echo "$(GREEN)make stop$(NC)             - Stop all running containers"
	@echo "$(GREEN)make logs$(NC)             - View container logs"
	@echo "$(GREEN)make clean$(NC)            - Remove containers and volumes"
	@echo "$(GREEN)make prune$(NC)            - Deep clean Docker system"
	@echo "$(GREEN)make test$(NC)             - Run tests"
	@echo "$(GREEN)make lint$(NC)             - Run code linting"

# Combined build and run command
build-and-run: prune
	@echo "$(YELLOW)Building and running environment...$(NC)"
	$(COMPOSE) build --pull
	$(COMPOSE) run --rm web python manage.py makemigrations
	$(COMPOSE) run --rm web python manage.py migrate
	$(COMPOSE) up

# Build containers
build: prune
	@echo "$(YELLOW)Building Docker containers...$(NC)"
	$(COMPOSE) build --pull --no-cache

# Run server
run: migrate
	@echo "$(YELLOW)Starting the server...$(NC)"
	$(COMPOSE) up

# Create new migrations
migrations:
	@echo "$(YELLOW)Creating new migrations...$(NC)"
	$(COMPOSE) run --rm web python manage.py makemigrations

# Apply database migrations
migrate:
	@echo "$(YELLOW)Applying migrations...$(NC)"
	$(COMPOSE) run --rm web python manage.py migrate

# Open Python shell
shell:
	@echo "$(YELLOW)Opening Python shell...$(NC)"
	$(COMPOSE) run --rm web python manage.py shell

# Stop all containers
stop:
	@echo "$(YELLOW)Stopping all containers...$(NC)"
	$(COMPOSE) down

# View container logs
logs:
	@echo "$(YELLOW)Viewing container logs...$(NC)"
	$(COMPOSE) logs -f

# Remove containers and volumes
clean:
	@echo "$(RED)Removing containers and volumes...$(NC)"
	$(COMPOSE) down -v --remove-orphans

# Deep clean Docker system
prune:
	@echo "$(RED)Deep cleaning Docker system...$(NC)"
	docker system prune -af

# Run tests
test:
	@echo "$(YELLOW)Running tests...$(NC)"
	$(COMPOSE) run --rm web python manage.py test

# Run code linting
lint:
	@echo "$(YELLOW)Running code linting...$(NC)"
	$(COMPOSE) run --rm web flake8
