# RBAC (Role-Based Access Control) Система

## Обзор

Система управления правами доступа на основе ролей (RBAC) для wb-service. Реализует:
- **Роли**: EMPLOYEE, CURATOR, ADMIN
- **Разрешения (permissions)**: детальные права на операции с ресурсами
- **Scope для кураторов**: доступ к конкретным подразделениям

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     API Controllers                          │
│  @CheckPermission / CheckPermissionDep / require_roles      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      RBAC Service                            │
│  check_role() / check_permission() / check_scope()          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     RBAC Repository                          │
│  Работа с БД: roles, permissions, user_roles, scopes        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Database Tables                           │
│  roles / permissions / role_permissions / user_roles        │
│  curator_scopes                                              │
└─────────────────────────────────────────────────────────────┘
```

## База данных

### Таблицы

#### `roles` - Роли
| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| name | VARCHAR(50) | Уникальное название (EMPLOYEE/CURATOR/ADMIN) |
| description | VARCHAR(255) | Описание роли |
| created_at | TIMESTAMP | Дата создания |

#### `permissions` - Разрешения
| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| name | VARCHAR(100) | Уникальное имя (news:create) |
| resource | VARCHAR(50) | Ресурс (news, comments, profile, documents) |
| action | VARCHAR(20) | Действие (create, read, update, delete, manage) |
| description | VARCHAR(255) | Описание |

#### `role_permissions` - Связь ролей и разрешений
| Колонка | Тип | Описание |
|---------|-----|----------|
| role_id | BIGINT | Foreign key → roles.id |
| permission_id | BIGINT | Foreign key → permissions.id |

#### `user_roles` - Связь пользователей и ролей
| Колонка | Тип | Описание |
|---------|-----|----------|
| user_eid | VARCHAR | EID пользователя (Keycloak ID) |
| role_id | BIGINT | Foreign key → roles.id |
| granted_by | VARCHAR | EID выдавшего роль |
| granted_at | TIMESTAMP | Дата выдачи |

#### `curator_scopes` - Scope для кураторов
| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| curator_eid | VARCHAR | EID куратора |
| org_unit_id | BIGINT | ID подразделения |

### Дефолтные роли и разрешения

#### Роли
| Роль | Описание |
|------|----------|
| EMPLOYEE | Базовый сотрудник (чтение новостей, комментарии) |
| CURATOR | Куратор с расширенными правами (создание/редактирование новостей) |
| ADMIN | Полный доступ ко всем функциям |

#### Разрешения по умолчанию

**News:**
- `news:create` - Создание новостей
- `news:read` - Чтение новостей
- `news:update` - Редактирование новостей
- `news:delete` - Удаление новостей
- `news:publish` - Публикация новостей

**Comments:**
- `comments:create` - Создание комментариев
- `comments:read` - Чтение комментариев
- `comments:delete` - Удаление комментариев

**Profile:**
- `profile:read` - Чтение профилей
- `profile:update` - Редактирование профилей

**Documents:**
- `documents:create` - Загрузка документов
- `documents:read` - Чтение документов
- `documents:delete` - Удаление документов

**Admin:**
- `users:manage` - Управление пользователями
- `roles:manage` - Управление ролями
- `permissions:manage` - Управление разрешениями

## Использование

### 1. Применение миграции

```bash
alembic upgrade head
```

### 2. Инициализация дефолтных данных

```bash
# Через API (требуется роль admin)
POST /api/v1/rbac/initialize
```

### 3. Способы проверки прав

#### Вариант A: Dependency (рекомендуется для CBV)

```python
from core.api.deps import CheckPermissionDep

@router.post("/")
async def create_news(
    data: NewsCreateSchema,
    _: None = Depends(CheckPermissionDep("news", "create")),
):
    ...
```

#### Вариант B: Декоратор (для функциональных view)

```python
from core.middleware import CheckPermission

@router.post("/")
@CheckPermission(resource="news", action="create")
async def create_news(data: NewsCreateSchema):
    ...
```

#### Вариант C: Старый способ (только роли)

```python
from core.api.deps import require_roles

@router.post("/")
async def create_news(
    data: NewsCreateSchema,
    current_user: CurrentUser = Depends(require_roles(["admin", "curator"])),
):
    ...
```

### 4. Проверка scope для кураторов

```python
from core.api.deps import RequireScopeDep

@router.patch("/{news_id}")
async def update_news(
    news_id: int,
    org_unit_id: int,
    _: None = Depends(RequireScopeDep("org_unit_id")),
):
    ...
```

### 5. Сервисный слой (программная проверка)

```python
from core.services.rbac_service import RBACService

rbac = RBACService(session)

# Проверка разрешения
has_perm = await rbac.check_permission(user_eid, "news", "create")

# Проверка роли
has_role = await rbac.check_role(user_eid, ["admin", "curator"])

# Проверка scope
has_scope = await rbac.check_scope(curator_eid, org_unit_id)

# Принудительная проверка (с исключением)
await rbac.enforce_permission(user_eid, "news", "create")
await rbac.enforce_scope(curator_eid, org_unit_id)
```

## API Endpoints

### Роли

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/api/v1/rbac/roles` | Все роли | admin |
| GET | `/api/v1/rbac/roles/{id}` | Роль по ID | admin, curator |
| POST | `/api/v1/rbac/roles` | Создать роль | admin |
| PUT | `/api/v1/rbac/roles/{id}` | Обновить роль | admin |
| DELETE | `/api/v1/rbac/roles/{id}` | Удалить роль | admin |

### Разрешения

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/api/v1/rbac/permissions` | Все разрешения | admin, curator |
| GET | `/api/v1/rbac/permissions/resource/{resource}` | По ресурсу | admin, curator |
| POST | `/api/v1/rbac/permissions` | Создать разрешение | admin |
| DELETE | `/api/v1/rbac/permissions/{id}` | Удалить разрешение | admin |

### Связи роль-разрешение

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/api/v1/rbac/roles/{id}/permissions` | Разрешения роли | admin, curator |
| POST | `/api/v1/rbac/roles/{id}/permissions/{perm_id}` | Добавить разрешение | admin |
| DELETE | `/api/v1/rbac/roles/{id}/permissions/{perm_id}` | Удалить разрешение | admin |

### Пользователь-роли

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/api/v1/rbac/users/{eid}/roles` | Роли пользователя | admin, hr |
| POST | `/api/v1/rbac/users/{eid}/roles/{role_id}` | Выдать роль | admin, hr |
| DELETE | `/api/v1/rbac/users/{eid}/roles/{role_id}` | Отобрать роль | admin, hr |
| DELETE | `/api/v1/rbac/users/{eid}/roles` | Все роли | admin, hr |

### Curator Scopes

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/api/v1/rbac/curators/{eid}/scopes` | Scope куратора | admin, hr, curator |
| POST | `/api/v1/rbac/curators/{eid}/scopes/{org_id}` | Добавить scope | admin, hr |
| DELETE | `/api/v1/rbac/curators/{eid}/scopes/{org_id}` | Удалить scope | admin, hr |

### Детальная информация

| Метод | Endpoint | Описание | Требуемая роль |
|-------|----------|----------|----------------|
| GET | `/api/v1/rbac/users/{eid}/detail` | Права пользователя | admin, hr |

## Матрица прав доступа

| Роль | news:read | news:create | news:update | news:delete | comments:* | documents:* | scope |
|------|-----------|-------------|-------------|-------------|------------|-------------|-------|
| EMPLOYEE | ✅ | ❌ | ❌ | ❌ | create, read | read | ❌ |
| CURATOR | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | все |

## Примеры использования

### Выдача роли пользователю

```bash
POST /api/v1/rbac/users/EID123/roles/2
Content-Type: application/json
Authorization: Bearer <admin_token>
```

### Добавление разрешения роли

```bash
POST /api/v1/rbac/roles/2/permissions/5
Authorization: Bearer <admin_token>
```

### Назначение scope куратору

```bash
POST /api/v1/rbac/curators/EID123/scopes/456
Authorization: Bearer <admin_token>
```

### Получение всех прав пользователя

```bash
GET /api/v1/rbac/users/EID123/detail
Authorization: Bearer <admin_token>
```

Ответ:
```json
{
  "user_eid": "EID123",
  "roles": [
    {
      "id": 2,
      "name": "CURATOR",
      "description": "Куратор с расширенными правами",
      "permissions": [
        {"name": "news:create", "resource": "news", "action": "create"},
        {"name": "news:update", "resource": "news", "action": "update"}
      ]
    }
  ],
  "curator_scopes": [
    {"id": 1, "curator_eid": "EID123", "org_unit_id": 456}
  ],
  "all_permissions": ["news:create", "news:update", "news:read"]
}
```

## Интеграция с Keycloak

Система RBAC дополняет Keycloak:
- **Keycloak**: аутентификация + базовые роли (admin, hr, employee)
- **RBAC**: детальные разрешения + scope для кураторов

### Сопоставление ролей

```python
ROLE_MAPPING = {
    "admin": ["ADMIN"],
    "hr": ["EMPLOYEE"],
    "employee": ["EMPLOYEE"],
    "news_editor": ["CURATOR"],
}
```

## Логика проверки прав

```
┌──────────────────────────────────────────┐
│  1. ADMIN роль → всегда доступ          │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│  2. Проверка required_roles             │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│  3. Проверка permission (resource:action)│
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│  4. Для кураторов: проверка scope       │
└──────────────────────────────────────────┘
```

## Файлы реализации

| Файл | Описание |
|------|----------|
| `core/models/rbac.py` | SQLAlchemy модели |
| `core/schemas/rbac_schema.py` | Pydantic схемы |
| `core/repositories/rbac_repo.py` | Репозиторий |
| `core/services/rbac_service.py` | Сервис |
| `core/middleware.py` | Декораторы CheckPermission, RequireScope |
| `core/api/deps.py` | Dependencies CheckPermissionDep, RequireScopeDep |
| `core/api/v1/rbac_controller.py` | API контроллер |
| `alembic/versions/a1b2c3d4e5f6_add_rbac_tables.py` | Миграция БД |
