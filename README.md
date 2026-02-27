## Название проекта

Организация мероприятий (EventManager).

## Описание идеи проекта

Приложение для планирования и организации мероприятий, которое помогает пользователям находить оптимальные программы сессий, размещения и активности на выбранной площадке. Приложение также рассчитывает общую стоимость участия в мероприятии, упрощая процесс организации. Это позволит пользователям быстро и удобно спланировать своё участие в конференциях, семинарах и других событиях.

## Описание предметной области

Сущности:
1. Пользователь
2. Мероприятие
3. Сессия
4. Площадка
5. Программа
6. Активности
7. Размещение

Роли:
1. Пользователь
2. Администратор

## Анализ аналогичных решений по минимум 3 критериям

|Название|Программа|Размещение|Активности| 
|--------|----------|-------------|--------------|
|Eventbrite|+|+|-| 
|Cvent|+|-|+|
|Мой проект|+|+|+|  

##5 Обоснование целесообразности и актуальности проекта 

Актуальность проекта заключается в упрощении планирования участия в мероприятиях, позволяя пользователям легко находить и бронировать программы сессий, размещение и активности в одном месте. С учётом растущего интереса к конференциям и деловым мероприятиям, создание удобного и функционального приложения становится необходимым. Это поможет пользователям сэкономить время и сделать процесс организации участия более комфортным.

##6 Описание акторов (ролей)

1. Пользователь: основной пользователь приложения, который планирует участие в мероприятиях.
2. Администратор -- обеспечивает актуальность и качество контента. Он отвечает за наполнение платформы информацией о размещении, активностях и программах мероприятий.

## Use-Case - диаграмма 

![uc](img/use_case.png)

## ER-диаграмма сущностей 

![er](img/er.png)

## Пользовательские сценарии

1. Зайти на основную страницу.
2. Авторизоваться, зайти на страницу своего профиля.
3. Зайти на страницу регистрации, зарегистрироваться или перейти на страницу авторизации.
4. Зайти на страницу авторизации, авторизироваться или перейти на страницу регистрации.
5. Посмотреть архив мероприятий.
6. Просмотреть официальные программы.
7. Записаться на сессию.
8. Посмотреть ближайшие запланированные активности в текущем мероприятии.
9. Поиск и фильтрация мероприятий.

## Формализация ключевых бизнес-процессов

![bpmn](img/bpmn.png)

## Технологический стек

* *Тип приложения* - Web MPA  
* *backend* - Python
* *frontend* - Python
* *database* - PostgreSQL  

## Верхнеуровневое разбиение на компоненты

![comp](img/comp.png)

## UML диаграммы классов для компонентов доступа к данным бизнес-логики

![uml](img/ppo.png)


## Запуск тестов

### Установка зависимостей

```bash
poetry install
```

### Запуск unit-тестов

```bash
# Стандартный запуск
poetry run pytest tests/unit -v

# Запуск в случайном порядке (используется по умолчанию через pytest-randomly)
poetry run pytest tests/unit -v --randomly-seed=random

# Запуск с фиксированным seed для воспроизводимости
poetry run pytest tests/unit -v --randomly-seed=42

# Запуск только "лондонских" тестов (с моками, работают без интернета)
poetry run pytest tests/unit -v -m unit
```

### Генерация отчёта Allure

```bash
# Запуск тестов с сохранением результатов для Allure
poetry run pytest tests/unit --alluredir=allure-results

# Открыть отчёт в браузере (требует установленного allure CLI)
allure serve allure-results
```

### Анализ процессов тестирования

По умолчанию pytest запускает **один процесс** на весь набор тестов. Все тест-файлы, классы и функции выполняются последовательно в этом одном процессе. Это конфигурируется через:
- `pyproject.toml` → `[tool.pytest.ini_options]`
- Плагин `pytest-xdist` (опция `-n auto`) позволяет запускать тесты параллельно в нескольких процессах

Текущая конфигурация: **1 процесс**, все 109 unit-тестов выполняются последовательно в одном запуске.

### Конфигурация pytest (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["src", "tests"]
addopts = "--tb=short -p randomly"   # краткие трейсбеки + случайный порядок тестов
```

### Анализ вариантов тестирования

- **"Лондонский" вариант (с моками)** — все тесты в `tests/unit/` используют `unittest.mock.Mock` и `AsyncMock` для изоляции сервисов от репозиториев. Работают без БД и без сети.
- **Классический вариант (без моков)** — тесты в `tests/integration/` используют реальные репозитории и реальную тестовую БД PostgreSQL (создаётся в `conftest.py` в изолированной схеме).

Запуск только классических тестов (требует PostgreSQL):
```bash
poetry run pytest tests/integration -v -m integration
```

### Запуск интеграционных тестов локально (через Docker)

```bash
# Поднять тестовую БД и запустить интеграционные тесты
docker compose run --rm integration-tests

# Или указать конкретный тест
docker compose run --rm integration-tests pytest tests/integration/venue_serv/ -v
```

### Запуск E2E-тестов

```bash
# Поднять всё окружение и запустить E2E
docker compose up -d db app mailhog
docker compose run --rm e2e-tests

# Для захвата сетевого трафика (профиль capture)
docker compose --profile capture up -d tcpdump
# После завершения тестов .pcap-файл будет в папке captures/
```

### Имитация MVP-сценария с помощью curl (для демонстрации E2E)

Ниже приведены те же шаги, что выполняет `test_mvp_event_flow_e2e.py`, но вручную через `curl`.

```bash
BASE=http://localhost:8000

# Шаг 1: Регистрация пользователя
curl -s -X POST $BASE/api/register \
  -H "Content-Type: application/json" \
  -d '{"fio":"Иван Иванов","number_passport":"1234567890","phone_number":"79261234567","email":"ivan@test.com","login":"demo_user1","password":"Test@Pass123","is_admin":false}'

# Шаг 2: Вход в систему
TOKEN=$(curl -s -X POST $BASE/api/login \
  -H "Content-Type: application/json" \
  -d '{"login":"demo_user1","password":"Test@Pass123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Шаг 3: Просмотр площадок
curl -s $BASE/venue.html | grep -o 'Москва\|Воронеж'

# Шаг 4: Создание мероприятия с маршрутом (Москва → Воронеж, Автомобиль)
USER_ID=$(curl -s $BASE/api/login \
  -H "Content-Type: application/json" \
  -d '{"login":"demo_user1","password":"Test@Pass123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['user_id'])")

curl -s -X POST $BASE/session/new \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"from_venue\":\"1\",\"to_venue\":\"2\",\"transport\":\"Автомобиль\",\"start_date\":\"05.05.2026\",\"end_date\":\"08.05.2026\",\"user_id\":\"$USER_ID\",\"activities[]\":[\"1\"],\"lodgings[]\":[\"1\"]}"

# Шаг 5: Проверка мероприятия
curl -s $BASE/event.html | grep -o 'Активное'
```

### Захват трафика с помощью tcpdump

```bash
# Запуск захвата трафика между приложением и e2e-тестами
docker compose --profile capture up -d tcpdump

# После прогона тестов остановить захват
docker compose stop tcpdump

# Файл captures/docker_traffic.pcap открывается в Wireshark
# или просматривается командой:
tcpdump -r captures/docker_traffic.pcap -nn -q
```

### Бенчмарк производительности (Лабораторная №3, №5)

**Лаба 3:** сравнение FastAPI vs Flask.  
**Лаба 5:** сравнение приложение vs трассировка/мониторинг/логирование.

Режимы (`benchmark/modes.json`):
- `no_tracing_info` — без трассировки, info-логи (базовый)
- `tracing_info` — с OpenTelemetry, info-логи
- `no_tracing_debug` — без трассировки, debug-логи
- `tracing_debug` — трассировка + debug-логи
- `flask` — альтернативный фреймворк

```bash
# 1. Создать сети (если ещё нет)
docker network create my_network 2>/dev/null || true
docker network create monitoring 2>/dev/null || true

# 1a. Перед первым запуском бенчмарка — сбросить БД (user1/123!e5T78 из seed):
docker compose down -v
docker compose up -d db app

# 2. Один режим (например, с трассировкой)
./benchmark/run_benchmark.sh tracing_info

# 3. Все режимы
./benchmark/run_benchmark.sh all

# 4. Быстрый прогон (60 сек)
BENCHMARK_QUICK=1 ./benchmark/run_benchmark.sh no_tracing_info

# 4a. Только сценарий логина (без ожидания json/medium/heavy)
BENCHMARK_SCENARIO=login BENCHMARK_QUICK=1 ./benchmark/run_benchmark.sh fastapi

# 5. Графики (требует matplotlib)
poetry run pip install matplotlib
poetry run python benchmark/plot_results.py results/*_report.json results/plots
```

Результаты: `results/*.csv`, `results/*_report.json`, `results/*_resources_report.json`  
При трассировке: `*_resources_full_report.json` — app + otel + jaeger (для отчёта Лабы 5)