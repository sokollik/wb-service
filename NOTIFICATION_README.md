# Notification & Band Bot Integration

## Обзор

Система уведомлений с интеграцией Band Bot для отправки push-уведомлений сотрудникам.

## Компоненты

```
┌─────────────────────────────────────────────────────────────┐
│                  API Controller                              │
│  GET/PUT/DELETE /api/notifications                          │
│  POST /api/notifications/bot/link                           │
│  GET  /api/notifications/bot/mapping                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              NotificationEventService                        │
│  notify_document_published()                                │
│  notify_acknowledgment_assigned()                           │
│  notify_status_change_draft_to_active()                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  BandBotAPIClient                            │
│  send_message() / send_document_notification()              │
│  send_news_notification() / send_birthday_notification()    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Database Tables                             │
│  notifications / user_bot_mappings                          │
│  notification_preferences                                    │
└─────────────────────────────────────────────────────────────┘
```

## База данных

### Таблица `notifications`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| user_eid | VARCHAR | EID пользователя |
| event_type | VARCHAR | Тип события |
| title | VARCHAR | Заголовок |
| message | VARCHAR | Текст уведомления |
| payload | JSONB | Дополнительные данные |
| is_read | BOOLEAN | Флаг прочтения |
| is_mandatory | BOOLEAN | Обязательное уведомление |
| created_at | TIMESTAMP | Дата создания |
| sent_at | TIMESTAMP | Время отправки push |
| delivered_at | TIMESTAMP | Время доставки push |

### Таблица `user_bot_mappings`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| user_eid | VARCHAR | EID пользователя (unique) |
| band_chat_id | VARCHAR | Chat ID в Band Bot |
| band_user_id | VARCHAR | User ID в Band |
| is_active | BOOLEAN | Активен ли маппинг |
| last_delivery_at | TIMESTAMP | Последняя успешная доставка |
| delivery_error_count | INTEGER | Счётчик ошибок |
| created_at | TIMESTAMP | Дата создания |
| updated_at | TIMESTAMP | Дата обновления |

### Таблица `notification_preferences`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| user_eid | VARCHAR | EID пользователя (unique) |
| channel_portal | BOOLEAN | Уведомления в портале |
| channel_email | BOOLEAN | Email уведомления |
| channel_messenger | BOOLEAN | Уведомления в Band Bot |
| digest_daily | BOOLEAN | Ежедневный дайджест |
| receive_news | BOOLEAN | Получать новости |
| receive_documents | BOOLEAN | Получать документы |
| receive_birthdays | BOOLEAN | Получать дни рождения |
| receive_comments | BOOLEAN | Получать комментарии |

## Типы уведомлений

```python
class NotificationType(str, Enum):
    # Новости
    NEWS_PUBLISHED = "NEWS_PUBLISHED"
    NEWS_MANDATORY_ACK = "NEWS_MANDATORY_ACK"
    
    # Документы
    DOCUMENT_PUBLISHED = "DOCUMENT_PUBLISHED"
    DOCUMENT_NEW_VERSION = "DOCUMENT_NEW_VERSION"
    DOCUMENT_ACKNOWLEDGMENT_ASSIGNED = "DOCUMENT_ACKNOWLEDGMENT_ASSIGNED"
    DOCUMENT_ACKNOWLEDGMENT_OVERDUE = "DOCUMENT_ACKNOWLEDGMENT_OVERDUE"
    
    # Комментарии
    COMMENT_ADDED = "COMMENT_ADDED"
    COMMENT_REPLY = "COMMENT_REPLY"
    
    # Дни рождения
    BIRTHDAY_TODAY = "BIRTHDAY_TODAY"
    BIRTHDAY_TOMORROW = "BIRTHDAY_TOMORROW"
    
    # Системные
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    SECURITY_ALERT = "SECURITY_ALERT"
```

## API Endpoints

### Основные операции с уведомлениями

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/notifications/` | Список уведомлений |
| GET | `/api/v1/notifications/stats` | Статистика уведомлений |
| GET | `/api/v1/notifications/unread-count` | Количество непрочитанных |
| GET | `/api/v1/notifications/{id}` | Уведомление по ID |
| POST | `/api/v1/notifications/{id}/read` | Отметить как прочитанное |
| POST | `/api/v1/notifications/read-all` | Отметить все как прочитанные |
| DELETE | `/api/v1/notifications/{id}` | Удалить уведомление |

### Настройки уведомлений

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/notifications/preferences` | Получить настройки |
| PATCH | `/api/v1/notifications/preferences` | Обновить настройки |

### Band Bot интеграция

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/notifications/bot/link` | Привязать Band аккаунт |
| GET | `/api/v1/notifications/bot/mapping` | Получить информацию о привязке |
| DELETE | `/api/v1/notifications/bot/unlink` | Отвязать Band аккаунт |
| POST | `/api/v1/notifications/bot/test` | Отправить тестовое уведомление |

## Генерация уведомлений

### 1. Публикация документа (DRAFT → ACTIVE)

```python
from core.services.notification_event_service import NotificationEventService

# В сервисе документов при смене статуса
await notification_service.notify_status_change_draft_to_active(
    document_id=doc_id,
    document_name="Приказ №123",
    old_status="DRAFT",
    new_status="ACTIVE",
)

# Также вызывается notify_document_published для всех сотрудников
await notification_service.notify_document_published(
    document_id=doc_id,
    document_name="Приказ №123",
    created_by=creator_eid,
)
```

### 2. Новая версия документа

```python
await notification_service.notify_document_new_version(
    document_id=doc_id,
    document_name="Приказ №123",
    version_number=2,
    users_to_notify=["EID001", "EID002"],  # Кто работал с документом
)
```

### 3. Назначение ознакомления

```python
# В DocumentAcknowledgmentService.assign_acknowledgment()
await self.notification_service.notify_acknowledgment_assigned(
    document_id=document_id,
    document_name="Приказ №123",
    employee_eid=employee_eid,
    required_at=datetime(2026, 4, 15, 23, 59, 59),
    assigned_by=assigned_by_eid,
)
```

### 4. Публикация новости

```python
await notification_service.notify_news_published(
    news_id=news_id,
    news_title="Новая новость",
    author_id=author_eid,
    is_mandatory=False,  # Или True для обязательного ознакомления
)
```

## Band Bot API

### Конфигурация

```python
# В settings.py
BAND_BOT_URL = "https://band.bot.corпоративный/api/v1"
BAND_BOT_TOKEN = "your-bot-token"
BAND_BOT_TIMEOUT = 30
```

### Отправка сообщения с кнопками

```python
from core.services.band_bot_client import band_bot_client

response = await band_bot_client.send_message(
    chat_id="CHAT123",
    title="📄 Новый документ",
    message="Вам назначено ознакомление с документом: Приказ №123",
    buttons=[
        [
            {"text": "📖 Ознакомиться", "url": "/documents/123/acknowledge"},
            {"text": "👁️ Просмотреть", "url": "/documents/123"},
        ]
    ],
    payload={"document_id": 123, "action": "acknowledge"},
)

if response.success:
    print(f"Сообщение отправлено: {response.message_id}")
else:
    print(f"Ошибка: {response.error}")
```

### Обработка ошибок доставки

```python
# В NotificationService.send_test_notification()
if response.success:
    mapping.last_delivery_at = datetime.utcnow()
    mapping.delivery_error_count = 0
else:
    mapping.delivery_error_count += 1
    # Деактивация после 5 ошибок
    if mapping.delivery_error_count >= 5:
        mapping.is_active = False
```

## Сценарии использования

### Сценарий 1: Пользователь привязывает Band Bot

```bash
# 1. Пользователь получает chat_id из Band Bot
# 2. Регистрирует его через API
POST /api/v1/notifications/bot/link
{
  "band_chat_id": "CHAT123456",
  "band_user_id": "USER789"
}

# 3. Проверяет привязку
GET /api/v1/notifications/bot/mapping

# 4. Отправляет тестовое уведомление
POST /api/v1/notifications/bot/test
```

### Сценарий 2: Назначение ознакомления с уведомлением

```
1. HR назначает ознакомление:
   POST /api/v1/documents/100/acknowledgment/assign
   {
     "employee_eids": ["EID001", "EID002"],
     "required_at": "2026-04-15T23:59:59"
   }

2. Система создаёт запись в document_acknowledgments

3. Система генерирует уведомление:
   - Создаётся запись в notifications
   - Отправляется push через Band Bot с кнопками

4. Сотрудник получает уведомление в Band:
   ┌─────────────────────────────────┐
   │ 📋 Требуется ознакомление       │
   │                                 │
   │ Вам назначено ознакомление с    │
   │ документом 'Приказ №123'        │
   │ до 15.04.2026                   │
   │                                 │
   │ [📖 Ознакомиться] [👁️ Просмотр]│
   └─────────────────────────────────┘
```

### Сценарий 3: Публикация документа

```
1. Документ меняет статус DRAFT → ACTIVE:
   PATCH /api/v1/documents/100
   {
     "status": "ACTIVE"
   }

2. NotificationEventService генерирует:
   - Уведомление создателю "Документ опубликован"
   - Уведомления всем сотрудникам "Новый документ"

3. Сотрудники получают push-уведомления
```

### Сценарий 4: Настройка уведомлений

```bash
# Пользователь отключает уведомления о днях рождения
PATCH /api/v1/notifications/preferences
{
  "receive_birthdays": false,
  "channel_messenger": true
}
```

## Миграция

```bash
# Применить миграцию
alembic upgrade head

# Миграция c3d4e5f6a7b8_add_notification_enhancements
```

## Файлы реализации

| Файл | Описание |
|------|----------|
| `core/models/notification.py` | Модели Notification, UserBotMapping, NotificationPreferences |
| `core/schemas/notification_schema.py` | Pydantic схемы |
| `core/repositories/notification_repo.py` | Репозиторий уведомлений |
| `core/services/notification_service.py` | Сервис уведомлений |
| `core/services/notification_event_service.py` | Генерация уведомлений при событиях |
| `core/services/band_bot_client.py` | Band Bot API клиент |
| `core/api/v1/notification_controller.py` | API контроллер |
| `alembic/versions/c3d4e5f6a7b8_add_notification_enhancements.py` | Миграция |

## Обработка ошибок

| Ошибка | Код | Действие |
|--------|-----|----------|
| Пользователь не найден в bot mappings | 403 | Запросить привязку аккаунта |
| Messenger notifications disabled | 403 | Проверить настройки уведомлений |
| Ошибка отправки Band Bot | 400 | Увеличить delivery_error_count |
| 5 последовательных ошибок | - | Деактивировать маппинг |

## Мониторинг

```sql
-- Количество непрочитанных уведомлений по пользователям
SELECT user_eid, COUNT(*) as unread_count
FROM notifications
WHERE is_read = false
GROUP BY user_eid
ORDER BY unread_count DESC;

-- Статистика доставки Band Bot
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE is_active = true) as active,
    COUNT(*) FILTER (WHERE delivery_error_count > 0) as with_errors
FROM user_bot_mappings;

-- Популярные типы уведомлений
SELECT event_type, COUNT(*) as count
FROM notifications
GROUP BY event_type
ORDER BY count DESC;
```
