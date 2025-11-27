ifeq ($(OS),Windows_NT)
    SLEEP := timeout
else
    SLEEP := sleep
endif

NAME ?= new_migration
TIME ?= 10m

## Запуск/Перезапуск проекта
start-dev:
	docker compose -f docker-compose.yaml down
	docker compose -f docker-compose.yaml up --build -d
	$(SLEEP) 3
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic upgrade head
	docker compose -f docker-compose.yaml exec database psql -U postgres -d postgres -f /dumps/main.sql

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