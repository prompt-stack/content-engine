.PHONY: help dev up down logs clean test

help:
	@echo "Content Engine - Development Commands"
	@echo ""
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs"
	@echo "  make logs-api    - View API logs"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make test        - Run tests"
	@echo "  make shell       - Open backend shell"
	@echo ""

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f backend

clean:
	docker-compose down -v
	rm -rf backend/__pycache__ backend/app/__pycache__

test:
	docker-compose exec backend pytest

shell:
	docker-compose exec backend bash

# Development shortcuts
dev: up logs-api