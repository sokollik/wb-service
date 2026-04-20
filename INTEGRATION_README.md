# Keycloak & Thesis Integration

## Обзор

Интеграция с корпоративными системами:
- **Keycloak SSO**: OAuth2/OIDC аутентификация, синхронизация пользователей, блокировка при увольнении
- **Thesis (Тезис)**: OAuth2/SAML SSO для перехода к документам, логирование переходов

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                  API Controllers                             │
│  /api/integrations/keycloak/webhook                         │
│  /api/integrations/thesis/document/{id}/link                │
│  /api/integrations/thesis/logs                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Integration Services                            │
│  KeycloakSSOService: validate_token, sync_user, webhook     │
│  ThesisIntegrationService: generate_link, log_transition    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Database Tables                             │
│  keycloak_user_sync / thesis_integration_logs              │
│  thesis_credentials                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Часть 1: Keycloak SSO

### Конфигурация

```bash
# .env
KEYCLOAK_SERVER_URL=http://keycloak:8080/auth
KEYCLOAK_REALM=wb-realm
KEYCLOAK_CLIENT_ID=wb-service
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
```

### OAuth2/OIDC Flow

```
1. Пользователь входит через Keycloak
   ↓
2. Keycloak возвращает JWT токен
   ↓
3. wb-service валидирует токен через RS256
   ↓
4. Извлечение EID/ФИО/email из payload
   ↓
5. Проверка is_fired (блокировка при увольнении)
   ↓
6. Доступ к ресурсам
```

### Валидация токена

```python
from core.services.integrations import KeycloakSSOService

sso_service = KeycloakSSOService(session)

try:
    payload = sso_service.validate_token(jwt_token)
    user_info = sso_service.extract_user_info(payload)
    
    # user_info содержит:
    # - eid: ID пользователя (sub)
    # - email: Email
    # - username: Username
    # - full_name: ФИО
    # - roles: Список ролей
except JWTError as e:
    # Токен невалиден
    raise HTTPException(401, f"Invalid token: {e}")
```

### Проверка увольнения

```python
# При каждом запросе проверяем статус пользователя
is_active = await sso_service.check_user_active(user_eid)

if not is_active:
    raise HTTPException(
        403,
        "Доступ заблокирован: пользователь уволен"
    )
```

### Webhook от Keycloak

**Настройка в Keycloak Admin Console:**
1. Realm Settings → Events → Event Listeners
2. Добавить `wb-service-webhook`
3. Admin URL: `https://wb-service/api/v1/integrations/keycloak/webhook`

**Формат запроса:**
```http
POST /api/v1/integrations/keycloak/webhook
X-Keycloak-Event: USER_DISABLED
Authorization: Bearer <webhook-secret>
Content-Type: application/json

{
  "userId": "EID123",
  "email": "user@company.com",
  "username": "user.name",
  "fullName": "Иванов Иван"
}
```

**Типы событий:**
| Событие | Описание | Действие |
|---------|----------|----------|
| `USER_CREATED` | Создание пользователя | Синхронизация |
| `USER_UPDATED` | Обновление данных | Синхронизация |
| `USER_DISABLED` | Блокировка (увольнение) | Установка is_fired=true |
| `USER_ENABLED` | Разблокировка | Установка is_fired=false |
| `USER_DELETED` | Удаление | Установка is_fired=true |

### Периодическая синхронизация

```python
# Cron job каждые 15 минут
from core.services.integrations import KeycloakSSOService

async def sync_users_job():
    sso_service = KeycloakSSOService(session)
    synced = await sso_service.periodic_sync(limit=100)
    print(f"Синхронизировано пользователей: {synced}")
```

---

## Часть 2: Thesis Integration

### Конфигурация

```bash
# .env
THESIS_BASE_URL=https://thesis.corporate.ru
THESIS_CLIENT_ID=wb-service-client
THESIS_CLIENT_SECRET=thesis-client-secret
THESIS_JWT_SECRET=jwt-secret-for-temp-tokens
```

### OAuth2 Flow для Тезис

```
1. Пользователь нажимает "Открыть в Тезис"
   ↓
2. wb-service получает OAuth2 token (Client Credentials)
   ↓
3. Генерация временного JWT (5 минут)
   ↓
4. Создание redirect URL с токенами
   ↓
5. Логирование перехода
   ↓
6. Редирект пользователя в Тезис
```

### API: Генерация ссылки на документ

**Запрос:**
```http
GET /api/v1/integrations/thesis/document/DOC-12345/link
Authorization: Bearer <user-jwt>
```

**Ответ:**
```json
{
  "redirect_url": "https://thesis.corporate.ru/documents/DOC-12345?token=<temp-jwt>&oauth_token=<oauth-token>",
  "thesis_document_id": "DOC-12345",
  "log_id": "1234567890",
  "expires_in": 300
}
```

**Использование:**
```python
import httpx

async def open_in_thesis(thesis_doc_id: str, user_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://wb-service/api/v1/integrations/thesis/document/{thesis_doc_id}/link",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        data = response.json()
        
        # Редирект пользователя
        return {"redirect": data["redirect_url"]}
```

### Логирование переходов

**Таблица `thesis_integration_logs`:**
- `user_eid` - кто перешёл
- `thesis_document_id` - ID в Тезис
- `local_document_id` - ID локального документа
- `status` - pending/success/failed
- `error_message` - ошибка если есть
- `created_at` - время запроса
- `completed_at` - время завершения

**API: Получение логов**
```http
GET /api/v1/integrations/thesis/logs?user_eid=EID123&status=success&limit=50
Authorization: Bearer <admin-token>
```

**Ответ:**
```json
{
  "total": 150,
  "logs": [
    {
      "id": 123,
      "user_eid": "EID123",
      "thesis_document_id": "DOC-456",
      "local_document_id": 789,
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-30T14:30:00",
      "completed_at": "2026-03-30T14:30:01"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**API: Статистика**
```http
GET /api/v1/integrations/thesis/stats
Authorization: Bearer <admin-token>
```

**Ответ:**
```json
{
  "total_transitions": 1500,
  "successful": 1450,
  "failed": 50,
  "success_rate": 96.67,
  "last_24_hours": 75
}
```

### Обработка ошибок

| Ошибка | Код | Действие |
|--------|-----|----------|
| Пользователь уволен | 403 | Блокировка перехода |
| Thesis credentials не настроены | 500 | Проверка конфигурации |
| OAuth2 token не получен | 502 | Повтор запроса |
| Тезис недоступен | 503 | Логирование ошибки |

---

## База данных

### `keycloak_user_sync`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| user_eid | VARCHAR | EID пользователя (unique) |
| email | VARCHAR | Email из Keycloak |
| username | VARCHAR | Username |
| full_name | VARCHAR | ФИО |
| is_active | BOOLEAN | Активен ли |
| is_fired | BOOLEAN | Уволен ли |
| fired_at | TIMESTAMP | Дата увольнения |
| last_sync_at | TIMESTAMP | Последняя синхронизация |

### `thesis_integration_logs`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| user_eid | VARCHAR | EID пользователя |
| thesis_document_id | VARCHAR | ID в Тезис |
| local_document_id | BIGINT | Локальный ID |
| access_token | TEXT | Временный токен |
| token_expires_at | TIMESTAMP | Истечение токена |
| redirect_url | TEXT | URL редиректа |
| status | VARCHAR | pending/success/failed |
| error_message | TEXT | Ошибка |
| created_at | TIMESTAMP | Время создания |
| completed_at | TIMESTAMP | Время завершения |

### `thesis_credentials`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| client_id | VARCHAR | OAuth2 Client ID |
| client_secret | VARCHAR | OAuth2 Secret |
| saml_entity_id | VARCHAR | SAML Entity ID |
| saml_acs_url | VARCHAR | SAML ACS URL |
| access_token | TEXT | Текущий токен |
| token_expires_at | TIMESTAMP | Истечение токена |
| is_active | BOOLEAN | Активны ли |

---

## API Endpoints

### Keycloak

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| POST | `/integrations/keycloak/webhook` | Webhook от Keycloak | - |
| POST | `/integrations/keycloak/sync` | Принудительная синхронизация | admin |

### Thesis

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/integrations/thesis/document/{id}/link` | Ссылка на документ | documents:read |
| GET | `/integrations/thesis/logs` | Логи переходов | admin |
| GET | `/integrations/thesis/stats` | Статистика | admin |

---

## Миграция

```bash
# Применить миграцию
alembic upgrade head

# Миграция: d4e5f6a7b8c9_add_keycloak_thesis_integrations
```

---

## Файлы реализации

| Файл | Описание |
|------|----------|
| `core/models/integrations.py` | Модели: KeycloakUserSync, ThesisIntegrationLog, ThesisCredentials |
| `core/services/integrations.py` | KeycloakSSOService, ThesisIntegrationService |
| `core/api/v1/integration_controller.py` | API контроллер |
| `core/config/settings.py` | Настройки интеграций |
| `alembic/versions/d4e5f6a7b8c9_add_keycloak_thesis_integrations.py` | Миграция |

---

## Безопасность

### Keycloak

1. **Валидация токена**: RS256 подпись
2. **Проверка увольнения**: Блокировка при is_fired=true
3. **Webhook secret**: Проверка Authorization заголовка

### Thesis

1. **OAuth2 Client Credentials**: Безопасное хранение client_secret
2. **Временные токены**: JWT с временем жизни 5 минут
3. **Логирование**: Все переходы логируются
4. **HTTPS**: Обязательное использование HTTPS

---

## Мониторинг

```sql
-- Активные пользователи Keycloak
SELECT COUNT(*) as active_users
FROM keycloak_user_sync
WHERE is_active = true AND is_fired = false;

-- Уволенные пользователи
SELECT COUNT(*) as fired_users
FROM keycloak_user_sync
WHERE is_fired = true;

-- Успешность переходов в Тезис
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM thesis_integration_logs
GROUP BY status;

-- Ошибки за последние 24 часа
SELECT 
    error_message,
    COUNT(*) as count
FROM thesis_integration_logs
WHERE status = 'failed' 
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY error_message
ORDER BY count DESC;
```

---

## Troubleshooting

### Keycloak: "Invalid token"

1. Проверьте KEYCLOAK_PUBLIC_KEY в .env
2. Убедитесь что ключ в правильном формате (BEGIN/END PUBLIC KEY)
3. Проверьте время на сервере (рассинхронизация времени)

### Thesis: "Credentials not configured"

1. Проверьте THESIS_CLIENT_ID и THESIS_CLIENT_SECRET
2. Убедитесь что запись в thesis_credentials существует и is_active=true
3. Проверьте доступность THESIS_BASE_URL

### Webhook не работает

1. Проверьте что Keycloak имеет доступ к /api/v1/integrations/keycloak/webhook
2. Проверьте логи wb-service на предмет ошибок
3. Убедитесь что заголовок X-Keycloak-Event передан
