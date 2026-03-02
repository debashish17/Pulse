.PHONY: help build up down logs shell test clean restart migrate health

# Default target
help:
	@echo "PULSE Docker Commands"
	@echo "====================="
	@echo ""
	@echo "Development:"
	@echo "  make build          Build Docker images"
	@echo "  make up             Start all services"
	@echo "  make down           Stop all services"
	@echo "  make restart        Restart PULSE app"
	@echo "  make logs           View logs (follow)"
	@echo "  make shell          Open bash in PULSE container"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run database migrations"
	@echo "  make db-shell       Open PostgreSQL shell"
	@echo "  make db-backup      Backup database"
	@echo "  make db-reset       Reset database (⚠️  deletes data)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all endpoint tests"
	@echo "  make test-real      Run real data tests"
	@echo "  make test-trending  Run trending discovery tests"
	@echo ""
	@echo "Maintenance:"
	@echo "  make health         Check service health"
	@echo "  make clean          Remove containers and images"
	@echo "  make prune          Clean up Docker system"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        Start production stack"
	@echo "  make prod-down      Stop production stack"
	@echo "  make prod-logs      View production logs"

# Development Commands
build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "API: http://localhost:8003"
	@echo "Docs: http://localhost:8003/docs"

down:
	docker-compose down
	@echo "✅ Services stopped"

restart:
	docker-compose restart pulse_app
	@echo "✅ PULSE app restarted"

logs:
	docker-compose logs -f pulse_app

logs-all:
	docker-compose logs -f

shell:
	docker-compose exec pulse_app bash

# Database Commands
migrate:
	docker-compose exec pulse_app alembic upgrade head
	@echo "✅ Migrations complete"

db-shell:
	docker-compose exec postgres psql -U pulse_user -d pulse_db

db-backup:
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U pulse_user pulse_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up to backups/"

db-reset:
	@echo "⚠️  This will DELETE all data. Press Ctrl+C to cancel..."
	@sleep 5
	docker-compose down -v
	docker-compose up -d
	@echo "✅ Database reset complete"

# Testing Commands
test:
	docker-compose exec pulse_app python test_all_endpoints.py

test-real:
	docker-compose exec pulse_app python test_real_data.py

test-trending:
	docker-compose exec pulse_app python test_trending_discovery.py

# Maintenance Commands
health:
	@echo "Checking PULSE health..."
	@curl -s http://localhost:8003/health | python -m json.tool
	@echo ""
	@echo "Checking PostgreSQL..."
	@docker-compose exec postgres pg_isready -U pulse_user -d pulse_db

clean:
	docker-compose down
	docker rmi pulse:latest pulse_app 2>/dev/null || true
	@echo "✅ Containers and images removed"

prune:
	docker system prune -f
	@echo "✅ Docker system cleaned"

# Production Commands
prod-up:
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo "✅ Production services started"

prod-down:
	docker-compose -f docker-compose.prod.yml down
	@echo "✅ Production services stopped"

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Quick commands
start: up
stop: down
log: logs
