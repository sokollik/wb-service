# 🚀 WB Service - Полный запуск

## ✅ Реализованный функционал

### 1. RBAC (Role-Based Access Control)
- Таблицы: roles, permissions, role_permissions, user_roles, curator_scopes
- Middleware: @CheckPermission, @RequireScope
- API: Управление ролями, разрешениями, scope для кураторов

### 2. Document Acknowledgment (Ознакомление с документами)
- Таблица: document_acknowledgments (required_at, acknowledged_at, acknowledged_by)
- API: Назначение ознакомления, отметка о прочтении, экспорт в Excel

### 3. Notifications & Band Bot
- Уведомления: DOCUMENT_PUBLISHED, ACKNOWLEDGMENT_ASSIGNED, и т.д.
- Интеграция: Band Bot API для push-уведомлений
- Таблицы: notifications, user_bot_mappings, notification_preferences

### 4. Keycloak & Thesis Integration
- Keycloak SSO: OAuth2/OIDC, webhook для синхронизации, блокировка при увольнении
- Thesis: OAuth2/SAML, генерация временных ссылок, логирование переходов

---

## 📋 Быстрый старт

### 1. Клонирование и настройка

```bash
cd c:\wb-service\wb\wb-service

# Скопируйте .env.example в .env
copy .env.example .env

# Отредактируйте .env с вашими значениями
notepad .env
```

### 2. Заполните обязательные переменные в .env

```bash
# Database
DB_USER=postgres
DB_PASS=postgres
DB_NAME=wb_db
DB_HOST=database
DB_PORT=5432

# Keycloak
KC_DB_NAME=keycloak_db
KC_DB_USER=keycloak
KC_DB_PASSWORD=keycloak_pass
KC_ADMIN_USERNAME=admin
KC_ADMIN_PASSWORD=admin

# Web
WEB_URL=http://localhost:3000
```

### 3. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка логов
docker-compose logs -f api
docker-compose logs -f keycloak

# Остановка
docker-compose down
```

### 4. Применение миграций

```bash
# Дождитесь запуска базы данных
docker-compose ps

# Примените все миграции
docker-compose exec api alembic upgrade head

# Проверьте применённые миграции
docker-compose exec api alembic current
```

### 5. Инициализация данных

```bash
# Инициализация RBAC (через API)
curl -X POST http://localhost:8000/api/v1/rbac/initialize \
  -H "Authorization: Bearer <admin-token>"

# Настройка Keycloak webhook
# В Keycloak Admin Console:
# Realm Settings → Events → Event Listeners → Add: wb-service-webhook
# Admin URL: http://api:8000/api/v1/integrations/keycloak/webhook
```

---

## 🔗 Сервисы

| Сервис | URL | Порт |
|--------|-----|------|
| API | http://localhost:8000 | 8000 |
| PostgreSQL | localhost | 5432 |
| Elasticsearch | http://localhost:9200 | 9200 |
| Keycloak | http://localhost:8080 | 8080 |
| Keycloak DB | localhost | 5433 (KC_DB_PORT) |

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🧪 Тестирование

### 1. Проверка RBAC

```bash
# Получить все роли (admin)
curl http://localhost:8000/api/v1/rbac/roles \
  -H "Authorization: Bearer <token>"

# Проверить права пользователя
curl http://localhost:8000/api/v1/rbac/users/EID123/detail \
  -H "Authorization: Bearer <token>"
```

### 2. Проверка уведомлений

```bash
# Получить уведомления
curl http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer <token>"

# Статистика
curl http://localhost:8000/api/v1/notifications/stats \
  -H "Authorization: Bearer <token>"

# Непрочитанные
curl http://localhost:8000/api/v1/notifications/unread-count \
  -H "Authorization: Bearer <token>"
```

### 3. Проверка Band Bot

```bash
# Привязать аккаунт
curl -X POST http://localhost:8000/api/v1/notifications/bot/link \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"band_chat_id": "CHAT123", "band_user_id": "USER456"}'

# Тестовое уведомление
curl -X POST http://localhost:8000/api/v1/notifications/bot/test \
  -H "Authorization: Bearer <token>"
```

### 4. Проверка Thesis Integration

```bash
# Получить ссылку на документ
curl http://localhost:8000/api/v1/integrations/thesis/document/DOC-123/link \
  -H "Authorization: Bearer <token>"

# Логи переходов
curl http://localhost:8000/api/v1/integrations/thesis/logs \
  -H "Authorization: Bearer <admin-token>"

# Статистика
curl http://localhost:8000/api/v1/integrations/thesis/stats \
  -H "Authorization: Bearer <admin-token>"
```

---

## 📁 Структура проекта

```
wb-service/
├── alembic/versions/           # Миграции БД
│   ├── a1b2c3d4e5f6_add_rbac_tables.py
│   ├── b2c3d4e5f6a7_add_document_acknowledgments.py
│   ├── c3d4e5f6a7b8_add_notification_enhancements.py
│   └── d4e5f6a7b8c9_add_keycloak_thesis_integrations.py
├── core/
│   ├── api/v1/                 # Контроллеры
│   │   ├── rbac_controller.py
│   │   ├── document_ack_controller.py
│   │   ├── notification_controller.py
│   │   └── integration_controller.py
│   ├── models/                 # ORM модели
│   │   ├── rbac.py
│   │   ├── notification.py
│   │   └── integrations.py
│   ├── repositories/           # Репозитории
│   ├── schemas/                # Pydantic схемы
│   ├── services/               # Бизнес-логика
│   │   ├── rbac_service.py
│   │   ├── document_acknowledgment_service.py
│   │   ├── notification_service.py
│   │   ├── notification_event_service.py
│   │   ├── band_bot_client.py
│   │   └── integrations.py
│   └── middleware.py           # Декораторы прав
├── RBAC_README.md              # Документация RBAC
├── DOCUMENT_ACKNOWLEDGMENT_README.md
├── NOTIFICATION_README.md
└── INTEGRATION_README.md
```

---

## 🔧 Troubleshooting

### Миграции не применяются

```bash
# Проверьте подключение к БД
docker-compose exec api python -c "from core.config.settings import get_database_settings; print(get_database_settings().url)"

# Откатите последнюю миграцию и примените заново
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic upgrade head
```

### Keycloak не запускается

```bash
# Проверьте логи
docker-compose logs keycloak

# Пересоздайте контейнер
docker-compose rm -f keycloak
docker-compose up -d keycloak
```

### Ошибки импорта в Python

```bash
# Проверьте синтаксис
docker-compose exec api python -m py_compile core/services/notification_service.py

# Проверьте зависимости
docker-compose exec api pip list | grep -E "fastapi|pydantic|sqlalchemy"
```

### Band Bot не отправляет уведомления

```bash
# Проверьте настройки
curl http://localhost:8000/api/v1/notifications/bot/mapping \
  -H "Authorization: Bearer <token>"

# Проверьте логи api
docker-compose logs api | grep -i "band"
```

---

## 📊 Мониторинг

### Проверка состояния сервисов

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи всех сервисов
docker-compose logs -f
```

### SQL запросы для проверки

```sql
-- Пользователи с ролями
SELECT u.user_eid, r.name as role_name
FROM user_roles u
JOIN roles r ON u.role_id = r.id;

-- Непрочитанные уведомления
SELECT user_eid, COUNT(*) as unread
FROM notifications
WHERE is_read = false
GROUP BY user_eid;

-- Ошибки доставки Band Bot
SELECT user_eid, delivery_error_count
FROM user_bot_mappings
WHERE delivery_error_count > 0;

-- Переходы в Тезис за сегодня
SELECT status, COUNT(*) as count
FROM thesis_integration_logs
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY status;
```

---

## 🎯 Следующие шаги

1. **Настройте Keycloak webhook** в Admin Console
2. **Зарегистрируйте Band Bot** и получите токен
3. **Настройте OAuth2 для Тезис** (client_id, client_secret)
4. **Протестируйте основные сценарии**:
   - Создание пользователя в Keycloak → синхронизация
   - Назначение ознакомления → уведомление в Band
   - Переход в Тезис → логирование

---

## 📚 Документация

- [RBAC](RBAC_README.md)
- [Document Acknowledgment](DOCUMENT_ACKNOWLEDGMENT_README.md)
- [Notifications](NOTIFICATION_README.md)
- [Integrations](INTEGRATION_README.md)
