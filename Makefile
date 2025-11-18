ifeq ($(OS),Windows_NT)
    SLEEP := timeout
else
    SLEEP := sleep
endif

NAME ?= new_migration
TIME ?= 10m

## Запуск/Перезапуск проекта
start-dev:
	@echo "--- Запуск DEV-окружения и применение миграций ---"
	docker compose -f docker-compose.yaml up --build -d
	# Увеличиваем ожидание, чтобы база данных успела инициализироваться
	$(SLEEP) 2
	# Запускаем миграции в контейнере 'api'
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic upgrade head

## Обновление базы данных (Применение новых миграций)
update-db-dev:
	@echo "--- Применение новых миграций к DEV базе данных ---"
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic upgrade head

## Создание новой миграции
# Использование: make new-migr name="my_new_feature"
new-migr:
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic revision --autogenerate -m "$(NAME)"
	docker compose -f docker-compose.yaml cp api:/app/alembic/versions ./alembic

## Пересоздание базы данных (Удаление данных)
rebuild-db:
	@echo "--- Пересоздание контейнера базы данных (данные будут удалены) ---"
	docker compose -f docker-compose.yaml rm database -fsv
	docker compose -f docker-compose.yaml up --build -d --no-deps database
	$(SLEEP) 2
	@echo "--- Применение миграций к новой БД ---"
	docker compose -f docker-compose.yaml exec -w /app api python -m alembic upgrade head

## Подключение к PostgreSQL (CLI)
see-db-dev:
	@echo "--- Подключение к psql ---"
	docker compose -f docker-compose.yaml exec database psql -U postgres

## Просмотр логов API
# Использование: make see-api-dev time=5m
see-api-dev:
	@echo "--- Логи API за последние $(TIME) ---"
	docker compose -f docker-compose.yaml logs -f api --since $(TIME)

## Создание дампа базы данных
dump-dev:
	@echo "--- Создание дампа базы данных в dumps/ ---"
	docker compose -f docker-compose.yaml exec database sh -c 'pg_dump -h 127.0.0.1 --username=postgres -d postgres > dumps/$$(date +'%Y-%m-%d_%H-%M-%S').dump'