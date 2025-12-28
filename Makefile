ifeq ($(OS),Windows_NT)
    SLEEP := timeout
else
    SLEEP := sleep
endif

NAME ?= new_migration
TIME ?= 10m

## Запуск/Перезапуск проекта
start-dev:
	docker compose -f docker-compose.yaml down -v
	docker compose -f docker-compose.yaml up -d database
	$(SLEEP) 5
	docker compose -f docker-compose.yaml run --rm api python -m alembic upgrade head
	docker compose -f docker-compose.yaml up -d elasticsearch api
	docker compose -f docker-compose.yaml exec database psql -U postgres -d postgres -f /docker-entrypoint-initdb.d/main.sql || true

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