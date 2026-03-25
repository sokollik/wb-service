ifeq ($(OS),Windows_NT)
    SLEEP := timeout
else
    SLEEP := sleep
endif

NAME ?= new_migration
TIME ?= 10m

.PHONY: help

help:
	@echo "Available commands:"
	@echo "  make start-dev        - Start all services with database migrations"
	@echo "  make start-quick      - Start all services (quick start without recreating volumes)"
	@echo "  make keycloak-info    - Show Keycloak configuration (Client Secret + Public Key)"
	@echo "  make reload-api       - Reload API container to apply new .env variables"
	@echo "  make update-db-dev    - Apply new migrations"
	@echo "  make new-migr         - Create new migration (use name=migration_name)"
	@echo "  make rebuild-db       - Rebuild database (WARNING: deletes data)"
	@echo "  make see-db-dev       - Connect to PostgreSQL CLI"
	@echo "  make see-api-dev      - Show API logs (use time=5m)"
	@echo "  make dump-dev         - Create database dump"
	@echo "  make down             - Stop all services"
	@echo "  make clean            - Remove all containers and volumes"

start-quick:
	docker compose -f docker-compose.yaml up -d
	@echo ""
	@echo "Services starting..."
	@echo "Waiting for Keycloak to initialize (this may take up to 60 seconds)..."
	@$(SLEEP) 20
	@docker compose logs keycloak-setup 2>/dev/null | tail -20 || echo "Keycloak is still initializing..."
	@echo ""
	@echo "Run 'make keycloak-info' to get Keycloak configuration"

keycloak-info:
	@echo "Keycloak Configuration:"
	@echo "======================="
	@docker compose logs keycloak-setup 2>/dev/null | grep -A 15 "Keycloak setup completed" || echo "Keycloak setup not completed yet. Please wait and try again."

## Запуск/Перезапуск проекта
start-dev:
	docker compose -f docker-compose.yaml down
	docker volume rm wb_data wb_elasticsearch_data 2>/dev/null || true
	docker compose -f docker-compose.yaml up -d database keycloak-db keycloak
	$(SLEEP) 10
	docker compose -f docker-compose.yaml run --rm api python -m alembic upgrade head
	docker compose -f docker-compose.yaml up -d elasticsearch api keycloak-setup
	docker compose -f docker-compose.yaml exec database psql -U postgres -d postgres -f /docker-entrypoint-initdb.d/main.sql || true
	@echo ""
	@echo "Waiting for Keycloak setup to complete..."
	@$(SLEEP) 30
	@make keycloak-info
	docker compose -f docker-compose.yaml up -d minio minio-setup

## Перезагрузка API с новыми ключами из .env
reload-api:
	@echo "Recreating API container to reload .env variables..."
	docker compose -f docker-compose.yaml up -d --force-recreate api
	@echo "API reloaded with new environment variables"

## Обновление базы данных (Применение новых миграций)
update-db-dev:
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic upgrade head

## Создание новой миграции
# Использование: make new-migr name="my_new_feature"
new-migr:
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic revision --autogenerate -m "$(NAME)"
	docker compose -f docker-compose.yaml cp api:/app/alembic/versions ./alembic

## Пересоздание базы данных (Удаление данных)
rebuild-db:
	docker compose -f docker-compose.yaml rm database -fsv
	docker compose -f docker-compose.yaml up --build -d --no-deps database
	$(SLEEP) 2
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic upgrade head

## Подключение к PostgreSQL (CLI)
see-db-dev:
	docker compose -f docker-compose.yaml exec database psql -U postgres

## Просмотр логов API
# Использование: make see-api-dev time=5m
see-api-dev:
	docker compose -f docker-compose.yaml logs -f api --since $(TIME)

## Создание дампа базы данных
dump-dev:
	docker compose -f docker-compose.yaml exec database sh -c 'pg_dump -h 127.0.0.1 --username=postgres -d postgres > dumps/$$(date +'%Y-%m-%d_%H-%M-%S').dump'

down:
	docker compose -f docker-compose.yaml down

clean:
	@echo "WARNING: This will remove all containers and volumes (all data will be lost)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose -f docker-compose.yaml down -v
	@echo "Cleanup completed"