# EventManager

Приложение для планирования участия в мероприятиях: пользователь выбирает площадки, формирует программу перемещения, добавляет размещение и активности, после чего работает с итоговой сессией и событием.

## Что в проекте сейчас

Проект относится к домену **мероприятий**, не путешествий. Основная бизнес-модель построена вокруг сессий и программ между площадками.

### Ключевые сущности

1. `users` — пользователи (участники и администраторы).
2. `venue` — площадки (города/локации).
3. `program` — программа перемещения между площадками:
   - `transfer_type`
   - `start_venue`
   - `end_venue`
   - `transfer_duration_minutes`
   - `cost`
4. `session` — сессия участия в мероприятии (`program + event + time range + type`).
5. `event` — мероприятие со статусом.
6. `activity` — активности внутри мероприятия.
7. `lodgings` — размещение.
8. Связи:
   - `users_event`
   - `event_activity`
   - `event_lodgings`

## Архитектура

- `src/routers` — HTTP-роуты (FastAPI).
- `src/controllers` — обработка входных данных и orchestration.
- `src/services` — бизнес-логика.
- `src/repository` — доступ к PostgreSQL.
- `src/models` — доменные модели (Pydantic).
- `templates` — MPA-шаблоны (Jinja2 + Materialize).
- `db-init` — SQL-схема, seed-данные, миграции.
- `tests` — unit / integration / e2e.

## Технологии

- Python 3.13
- FastAPI
- SQLAlchemy (async) + asyncpg
- PostgreSQL
- Jinja2
- Pytest (+ asyncio, xdist, randomly)
- Docker Compose
- OpenTelemetry + Jaeger + Prometheus (опционально)

## Запуск локально (без Docker для app)

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Поднять PostgreSQL

```bash
docker compose up -d db
```

По умолчанию приложение читает строку подключения из `config.cfg` (`DATABASE_URL_ASYNC`) или из переменной окружения `DATABASE_URL`.

### 3. Запуск приложения

```bash
poetry run uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

После запуска:
- UI: `http://localhost:8000/`
- Healthcheck: `http://localhost:8000/health`

## Запуск через Docker Compose

В `docker-compose.yml` сети `my_network` и `monitoring` объявлены как external, создайте их один раз:

```bash
docker network create my_network
docker network create monitoring
```

Запуск приложения и БД:

```bash
docker compose up -d db app
```

## Тесты

### Unit

```bash
poetry run pytest tests/unit -v -m unit
```

### Integration

```bash
poetry run pytest tests/integration -v
```

Если запускаешь интеграционные тесты локально через `docker compose` (сервис `test-db`), используй порт `5435` и явный `DATABASE_URL`.

PowerShell:
```powershell
$env:DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5435/test_db"
poetry run pytest tests/integration -v
```

Bash:
```bash
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5435/test_db poetry run pytest tests/integration -v
```

### E2E

```bash
docker compose up -d db app mailhog
docker compose --profile test run --rm e2e-tests
```

### Тесты в Docker-профиле `test`

```bash
docker compose --profile test run --rm unit-tests
docker compose --profile test run --rm integration-tests
```

## Отчёты Allure

```bash
poetry run pytest tests/unit --alluredir=allure-results
allure serve allure-results
```

Либо сервисом из compose:

```bash
docker compose up -d allure
```

## Наблюдаемость и бенчмарк

### Tracing (Jaeger + OTel Collector)

```bash
docker compose --profile tracing up -d jaeger otel-collector
```

### Benchmark

```bash
docker compose --profile benchmark run --rm benchmark
```

## Важные роуты

- `/program.html` — управление программами перемещения.
- `/session.html` — управление сессиями.
- `/event.html` — управление мероприятиями.
- `/venue.html` — площадки.
- `/activity.html` — активности.
- `/lodging.html` — размещение.
- `/programs/official` — каталог официальных программ.
- `/programs/recommended` — каталог рекомендованных программ.

Легаси-алиасы сохранены для совместимости:
- `/tours` → `/programs/official`
- `/recommended` → `/programs/recommended`


