# Document Acknowledgment System

## Обзор

Система ознакомления сотрудников с документами. Позволяет назначать обязательное ознакомление с документами и отслеживать статус выполнения.

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                  API Controller                              │
│  /documents/{id}/acknowledgment/assign                      │
│  /documents/{id}/acknowledge                                │
│  /documents/{id}/acknowledgments                            │
│  /documents/acknowledgments/export                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              DocumentAcknowledgmentService                   │
│  assign_acknowledgment() / acknowledge_document()           │
│  get_document_acknowledgments() / get_for_export()          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│          DocumentAcknowledgmentRepository                    │
│  CRUD операции с таблицей document_acknowledgments          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Database Table                              │
│  document_acknowledgments                                    │
└─────────────────────────────────────────────────────────────┘
```

## База данных

### Таблица `document_acknowledgments`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | Primary key |
| document_id | BIGINT | Foreign key → documents.id |
| employee_eid | VARCHAR | EID сотрудника, который должен ознакомиться |
| required_at | TIMESTAMP | Дата/время когда требуется ознакомление |
| acknowledged_at | TIMESTAMP | Дата фактического ознакомления (NULL если не ознакомлен) |
| acknowledged_by | VARCHAR | EID сотрудника, который ознакомился |
| created_at | TIMESTAMP | Дата создания записи |

### Индексы
- `ix_document_acknowledgments_document_id`
- `ix_document_acknowledgments_employee_eid`
- `ix_document_acknowledgments_acknowledged_at`
- `ix_document_acknowledgments_required_at`

### Уникальные ограничения
- `uq_document_employee` - уникальная пара (document_id, employee_eid)

## API Endpoints

### 1. Назначить ознакомление

```http
POST /api/v1/documents/{document_id}/acknowledgment/assign
Content-Type: application/json
Authorization: Bearer <token>
```

**Требуемые права:** `documents:manage` или роли `admin`, `curator`

**Request Body:**
```json
{
  "employee_eids": ["EID001", "EID002", "EID003"],
  "required_at": "2026-04-15T23:59:59"
}
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "document_id": 100,
    "employee_eid": "EID001",
    "required_at": "2026-04-15T23:59:59",
    "acknowledged_at": null,
    "acknowledged_by": null,
    "created_at": "2026-03-30T12:00:00"
  }
]
```

### 2. Отметить ознакомление

```http
POST /api/v1/documents/{document_id}/acknowledge?employee_eid={eid}
Authorization: Bearer <token>
```

**Требуемые права:** `documents:read`

**Query Parameters:**
- `employee_eid` (required): EID сотрудника, который ознакомился

**Response:** `200 OK`
```json
{
  "id": 1,
  "document_id": 100,
  "employee_eid": "EID001",
  "required_at": "2026-04-15T23:59:59",
  "acknowledged_at": "2026-03-30T14:30:00",
  "acknowledged_by": "EID001",
  "created_at": "2026-03-30T12:00:00"
}
```

### 3. Получить ознакомления документа

```http
GET /api/v1/documents/{document_id}/acknowledgments?limit=100&offset=0
Authorization: Bearer <token>
```

**Требуемые права:** `documents:read`

**Query Parameters:**
- `limit` (optional): Количество записей (default: 100)
- `offset` (optional): Смещение (default: 0)

**Response:** `200 OK`
```json
{
  "total": 50,
  "acknowledgments": [
    {
      "id": 1,
      "document_id": 100,
      "employee_eid": "EID001",
      "required_at": "2026-04-15T23:59:59",
      "acknowledged_at": "2026-03-30T14:30:00",
      "acknowledged_by": "EID001",
      "created_at": "2026-03-30T12:00:00",
      "document_name": "Приказ №123",
      "is_overdue": false
    }
  ]
}
```

### 4. Получить ознакомления сотрудника

```http
GET /api/v1/documents/acknowledgments/employee/{employee_eid}?status=pending&limit=100
Authorization: Bearer <token>
```

**Требуемые права:** `documents:read` + роли `admin`, `hr`, `curator`

**Query Parameters:**
- `status` (optional): `pending`, `acknowledged`, `overdue`
- `limit` (optional): Количество записей (default: 100)

### 5. Получить статус сотрудника

```http
GET /api/v1/documents/acknowledgments/employee/{employee_eid}/status
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "employee_eid": "EID001",
  "total_documents": 10,
  "acknowledged_count": 7,
  "pending_count": 3,
  "overdue_count": 1
}
```

### 6. Удалить ознакомление

```http
DELETE /api/v1/documents/acknowledgments/{acknowledgment_id}
Authorization: Bearer <token>
```

**Требуемые права:** `documents:manage` + роли `admin`, `curator`

### 7. Экспорт в Excel

```http
GET /api/v1/documents/acknowledgments/export?document_id=100&status=pending
Authorization: Bearer <token>
```

**Требуемые права:** `documents:manage` + роли `admin`, `curator`

**Query Parameters:**
- `document_id` (optional): Фильтр по документу
- `employee_eid` (optional): Фильтр по сотруднику
- `status` (optional): `pending`, `acknowledged`, `overdue`

**Response:** `200 OK`
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename=document_acknowledgments.xlsx`

**Содержимое Excel:**
| ID | ID документа | Название документа | EID сотрудника | ФИО сотрудника | Требуется до | Ознакомлен | Ознакомил (EID) | Статус | Просрочено |
|----|--------------|-------------------|----------------|----------------|--------------|------------|-----------------|--------|------------|
| 1 | 100 | Приказ №123 | EID001 | Иванов И.И. | 15.04.2026 23:59 | 30.03.2026 14:30 | EID001 | Ознакомлен | Нет |

## Статусы ознакомления

| Статус | Описание |
|--------|----------|
| `pending` | Ожидается ознакомление (required_at в будущем или настоящем) |
| `acknowledged` | Сотрудник ознакомился (acknowledged_at не NULL) |
| `overdue` | Просрочено (acknowledged_at NULL и required_at в прошлом) |

## Сценарии использования

### Сценарий 1: Назначение ознакомления с приказом

```python
# HR назначает ознакомление с новым приказом
POST /api/v1/documents/100/acknowledgment/assign
{
  "employee_eids": ["EID001", "EID002", "EID003"],
  "required_at": "2026-04-15T23:59:59"
}
```

### Сценарий 2: Сотрудник ознакамливается с документом

```python
# Сотрудник заходит в документ и нажимает "Ознакомлен"
POST /api/v1/documents/100/acknowledge?employee_eid=EID001
```

### Сценарий 3: Проверка кто не ознакомился

```python
# Руководитель получает список неознакомленных
GET /api/v1/documents/100/acknowledgments

# Или экспорт в Excel для отчёта
GET /api/v1/documents/acknowledgments/export?document_id=100&status=pending
```

### Сценарий 4: Проверка задолженности сотрудника

```python
# HR проверяет какие документы не ознакомил сотрудник
GET /api/v1/documents/acknowledgments/employee/EID001?status=overdue
```

## Интеграция с RBAC

Система использует RBAC для проверки прав:

| Операция | Required Permission | Required Roles |
|----------|--------------------|----------------|
| Назначить ознакомление | `documents:manage` | admin, curator |
| Отметить ознакомление | `documents:read` | - |
| Просмотр ознакомлений | `documents:read` | - |
| Просмотр сотрудника | `documents:read` | admin, hr, curator |
| Удаление ознакомления | `documents:manage` | admin, curator |
| Экспорт в Excel | `documents:manage` | admin, curator |

## Файлы реализации

| Файл | Описание |
|------|----------|
| `core/models/document.py` | Модель `DocumentAcknowledgment` |
| `core/schemas/document_schema.py` | Pydantic схемы |
| `core/repositories/document_repo.py` | `DocumentAcknowledgmentRepository` |
| `core/services/document_acknowledgment_service.py` | Бизнес-логика |
| `core/services/document_export_service.py` | Экспорт в Excel |
| `core/api/v1/document_ack_controller.py` | API контроллер |
| `alembic/versions/b2c3d4e5f6a7_add_document_acknowledgments.py` | Миграция БД |

## Применение миграции

```bash
alembic upgrade head
```

## Примеры кода

### Назначение ознакомления (Python)

```python
import httpx

async def assign_acknowledgment(document_id: int, employee_eids: list, required_at: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://api/api/v1/documents/{document_id}/acknowledgment/assign",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "employee_eids": employee_eids,
                "required_at": required_at
            }
        )
        return response.json()
```

### Отметка об ознакомлении

```python
async def acknowledge_document(document_id: int, employee_eid: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://api/api/v1/documents/{document_id}/acknowledge",
            params={"employee_eid": employee_eid},
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### Получение статистики сотрудника

```python
async def get_employee_status(employee_eid: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://api/api/v1/documents/acknowledgments/employee/{employee_eid}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```
