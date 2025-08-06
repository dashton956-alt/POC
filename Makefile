# NetBox Orchestrator POC Makefile
# Simplifies common development and deployment tasks

.PHONY: help install start stop restart logs clean test lint format docs backup restore

# Default target
help:
	@echo "NetBox Orchestrator POC - Available Commands:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make install          - Install dependencies and setup environment"
	@echo "  make start           - Start all services"
	@echo "  make stop            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make dev             - Start in development mode"
	@echo "  make logs            - View logs from all services"
	@echo "  make shell           - Open shell in orchestrator container"
	@echo "  make netbox-shell    - Open shell in NetBox container"
	@echo "  make db-shell        - Open database shell"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make lint            - Run code linting"
	@echo "  make format          - Format code with Black"
	@echo "  make type-check      - Run type checking with mypy"
	@echo ""
	@echo "📊 Data Management:"
	@echo "  make import-devices  - Import device types"
	@echo "  make backup          - Backup databases"
	@echo "  make restore         - Restore from backup"
	@echo "  make reset           - Reset all data (DESTRUCTIVE)"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  make docs            - Generate documentation"
	@echo "  make docs-serve      - Serve documentation locally"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean           - Clean up containers and volumes"
	@echo "  make clean-all       - Clean everything including images"
	@echo "  make update          - Update all services"
	@echo "  make health          - Check service health"

# Installation and setup
install:
	@echo "🔧 Installing dependencies..."
	pip install -r requirements.txt
	@echo "📝 Setting up environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please customize it"; fi
	@echo "✅ Installation complete!"

# Service management
start:
	@echo "🚀 Starting NetBox services..."
	cd netbox && docker-compose up -d
	@echo "🚀 Starting Orchestrator services..."
	cd example-orchestrator && docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	sleep 30
	@make health

start-netbox:
	@echo "🚀 Starting NetBox services..."
	cd netbox && docker-compose up -d

start-orchestrator:
	@echo "🚀 Starting Orchestrator services..."
	cd example-orchestrator && docker-compose up -d

stop:
	@echo "🛑 Stopping all services..."
	cd example-orchestrator && docker-compose down
	cd netbox && docker-compose down

restart: stop start

dev:
	@echo "🔧 Starting development environment..."
	cd netbox && docker-compose -f docker-compose.yml -f ../docker-compose.dev.yml up -d
	cd example-orchestrator && docker-compose -f docker-compose.yml -f ../docker-compose.dev.yml up -d

# Logging and monitoring
logs:
	@echo "📋 Showing logs for all services..."
	cd netbox && docker-compose logs -f &
	cd example-orchestrator && docker-compose logs -f

logs-netbox:
	cd netbox && docker-compose logs -f

logs-orchestrator:
	cd example-orchestrator && docker-compose logs -f

logs-tail:
	@echo "📋 Tailing logs (last 100 lines)..."
	cd netbox && docker-compose logs --tail=100 -f

# Shell access
shell:
	@echo "🐚 Opening orchestrator shell..."
	cd example-orchestrator && docker-compose exec orchestrator bash

netbox-shell:
	@echo "🐚 Opening NetBox shell..."
	cd netbox && docker-compose exec netbox bash

db-shell:
	@echo "🗄️ Opening database shell..."
	cd example-orchestrator && docker-compose exec postgres psql -U orchestrator

netbox-db-shell:
	@echo "🗄️ Opening NetBox database shell..."
	cd netbox && docker-compose exec postgres psql -U netbox

redis-shell:
	@echo "📦 Opening Redis shell..."
	cd example-orchestrator && docker-compose exec redis redis-cli -p 6380

# Testing
test:
	@echo "🧪 Running all tests..."
	python -m pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	python -m pytest tests/unit/ -v

test-integration:
	@echo "🧪 Running integration tests..."
	python -m pytest tests/integration/ -v

test-coverage:
	@echo "📊 Running tests with coverage..."
	python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "🔍 Running linting..."
	flake8 . --exclude=venv,devicetype-library,netbox,example-orchestrator/migrations
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting code..."
	black . --exclude="/(venv|devicetype-library|netbox)/"
	@echo "✅ Code formatted!"

type-check:
	@echo "🔍 Running type checking..."
	mypy . --exclude="/(venv|devicetype-library|netbox)/"
	@echo "✅ Type checking complete!"

quality-check: lint type-check
	@echo "✅ All quality checks passed!"

# Data management
import-devices:
	@echo "📥 Importing device types..."
	python device_import.py
	@echo "✅ Device import complete!"

import-devices-dry:
	@echo "📥 Dry run - importing device types..."
	python device_import.py --dry-run

import-cisco:
	@echo "📥 Importing Cisco device types..."
	python device_import.py --vendor cisco

# Backup and restore
backup:
	@echo "💾 Creating backup..."
	mkdir -p backups
	@echo "Backing up orchestrator database..."
	cd example-orchestrator && docker-compose exec -T postgres pg_dump -U orchestrator orchestrator > ../backups/orchestrator-$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backing up NetBox database..."
	cd netbox && docker-compose exec -T postgres pg_dump -U netbox netbox > ../backups/netbox-$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup complete!"

restore:
	@echo "🔄 Restoring from backup..."
	@echo "Available backups:"
	@ls -la backups/
	@echo "Use: make restore-file FILE=backups/filename.sql"

restore-file:
	@if [ -z "$(FILE)" ]; then echo "❌ Please specify FILE=path/to/backup.sql"; exit 1; fi
	@echo "🔄 Restoring from $(FILE)..."
	@if echo $(FILE) | grep -q orchestrator; then \
		cd example-orchestrator && docker-compose exec -T postgres psql -U orchestrator orchestrator < ../$(FILE); \
	elif echo $(FILE) | grep -q netbox; then \
		cd netbox && docker-compose exec -T postgres psql -U netbox netbox < ../$(FILE); \
	else \
		echo "❌ Cannot determine database from filename"; \
	fi
	@echo "✅ Restore complete!"

# Health checks
health:
	@echo "🏥 Checking service health..."
	@echo "NetBox:"
	@curl -s http://localhost:8000/api/ > /dev/null && echo "  ✅ NetBox API responding" || echo "  ❌ NetBox API not responding"
	@echo "Orchestrator:"
	@curl -s http://localhost:8080/health > /dev/null && echo "  ✅ Orchestrator API responding" || echo "  ❌ Orchestrator API not responding"
	@echo "Orchestrator UI:"
	@curl -s http://localhost:3000 > /dev/null && echo "  ✅ Orchestrator UI responding" || echo "  ❌ Orchestrator UI not responding"
	@echo "Container status:"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | head -20

status: health

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@if [ -d "docs" ]; then \
		cd docs && mkdocs build; \
	else \
		echo "No docs directory found"; \
	fi

docs-serve:
	@echo "📚 Serving documentation at http://localhost:8085..."
	@if [ -d "docs" ]; then \
		cd docs && mkdocs serve -a 0.0.0.0:8085; \
	else \
		echo "No docs directory found"; \
	fi

# Cleanup
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	cd example-orchestrator && docker-compose down -v
	cd netbox && docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

clean-all: clean
	@echo "🧹 Removing all images..."
	docker image prune -a -f
	docker volume prune -f

reset:
	@echo "⚠️  This will DESTROY all data! Are you sure? (y/N)"
	@read -p "" confirm; if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "🔥 Resetting all data..."; \
		make clean-all; \
		make start; \
		echo "✅ Reset complete!"; \
	else \
		echo "❌ Reset cancelled"; \
	fi

# Updates
update:
	@echo "🔄 Updating all services..."
	cd netbox && docker-compose pull
	cd example-orchestrator && docker-compose pull
	make restart
	@echo "✅ Update complete!"

update-images:
	@echo "🔄 Pulling latest images..."
	cd netbox && docker-compose pull
	cd example-orchestrator && docker-compose pull

# Git operations
git-status:
	@echo "📊 Git status:"
	git status --short

git-commit:
	@echo "💾 Committing changes..."
	git add .
	@read -p "Commit message: " msg; git commit -m "$$msg"

git-push:
	@echo "🚀 Pushing to remote..."
	git push origin main

# Development helpers
dev-setup: install
	@echo "🔧 Setting up development environment..."
	@if [ ! -f docker-compose.override.yml ]; then cp docker-compose.dev.yml docker-compose.override.yml; fi
	@echo "✅ Development setup complete!"

requirements:
	@echo "📦 Updating requirements..."
	pip freeze > requirements.txt

check-ports:
	@echo "🔍 Checking port usage..."
	@echo "Port 8000 (NetBox):"
	@ss -tulpn | grep :8000 || echo "  Available"
	@echo "Port 8080 (Orchestrator API):"
	@ss -tulpn | grep :8080 || echo "  Available"
	@echo "Port 3000 (Orchestrator UI):"
	@ss -tulpn | grep :3000 || echo "  Available"

# Monitoring
monitor:
	@echo "📊 Service monitoring..."
	watch -n 5 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Performance testing
perf-test:
	@echo "⚡ Running performance tests..."
	@if command -v hey > /dev/null; then \
		hey -n 100 -c 10 http://localhost:8000/api/; \
		hey -n 100 -c 10 http://localhost:8080/health; \
	else \
		echo "Install 'hey' for performance testing: go install github.com/rakyll/hey@latest"; \
	fi

# Environment info
info:
	@echo "ℹ️  System Information:"
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo "Python version: $(shell python --version)"
	@echo "Git version: $(shell git --version)"
	@echo "Current directory: $(shell pwd)"
	@echo "Available disk space: $(shell df -h . | tail -1 | awk '{print $$4}')"

# Quick development cycle
dev-cycle: format lint test
	@echo "✅ Development cycle complete!"

# CI/CD helpers
ci-test: install test lint
	@echo "✅ CI tests complete!"

# Production deployment helpers
prod-check:
	@echo "🔍 Production readiness check..."
	@echo "Checking environment variables..."
	@grep -q "DEBUG=false" .env && echo "  ✅ Debug disabled" || echo "  ⚠️  Debug should be disabled"
	@grep -q "SECRET_KEY=" .env && echo "  ✅ Secret key configured" || echo "  ❌ Secret key not configured"
	@echo "Checking SSL certificates..."
	@test -f ssl/cert.pem && echo "  ✅ SSL certificate found" || echo "  ⚠️  SSL certificate not found"
