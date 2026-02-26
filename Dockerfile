# # FROM python:3.13-slim

# # # Переменные окружения
# # ENV POETRY_HOME="/opt/poetry" \
# #     PATH="/opt/poetry/bin:$PATH" \
# #     PYTHONPATH=/app/src

# # WORKDIR /app

# # # Системные зависимости
# # RUN apt-get update && apt-get install -y \
# #     curl wget unzip gcc python3-dev \
# #     postgresql-client libpq5 \
# #     && rm -rf /var/lib/apt/lists/* \
# #     && apt-get clean

# # RUN pip install --no-cache-dir --timeout=100 poetry

# # # Копируем зависимости
# # COPY pyproject.toml poetry.lock ./

# # # Установка всех зависимостей
# # RUN poetry config virtualenvs.create false \
# #     && poetry install --no-root --no-interaction --no-ansi

# # # Установка Allure
# # RUN wget -q https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.tgz \
# #     && tar -zxvf allure-2.27.0.tgz -C /opt/ \
# #     && ln -s /opt/allure-2.27.0/bin/allure /usr/local/bin/allure \
# #     && rm allure-2.27.0.tgz

# # RUN poetry install --no-root

# # COPY . /app

# # # Создаем папки
# # RUN mkdir -p /app/logs /app/templates /app/static /app/allure-results /app/test-reports /app/profiles

# # RUN pip install allure-pytest==2.15.0
# # # Health check
# # HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
# #     CMD curl -f http://localhost:8000/health || exit 1

# # EXPOSE 8000

# # CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# FROM python:3.13-slim
# ENV POETRY_HOME="/opt/poetry" \
#     PATH="/opt/poetry/bin:$PATH" \
#     PYTHONPATH=/app/src
# # Системные зависимости
# RUN apt-get update && apt-get install -y \
#     curl wget unzip gcc python3-dev \
#     postgresql-client libpq5 docker.io \
#     && rm -rf /var/lib/apt/lists/*
# # Poetry
# RUN pip install --no-cache-dir poetry

# WORKDIR /app

# # Копируем только зависимости
# COPY pyproject.toml poetry.lock /app/

# # Установка зависимостей в системный Python (virtualenv false)
# RUN poetry config virtualenvs.create false \
#     && poetry install --no-root --no-interaction --no-ansi  --with dev

# RUN poetry add --dev allure-pytest

# RUN pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry.instrumentation.requests opentelemetry.instrumentation.httpx 
# # Копируем весь проект
# COPY . /app

# # Опционально создаём нужные папки
# RUN mkdir -p /app/logs /app/templates /app/static /app/allure-results /app/test-reports /app/profiles

# # EXPOSE
# EXPOSE 8000


# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Dockerfile для CI/CD и локального запуска с OpenTelemetry и Allure

FROM python:3.13-slim

# ------------------------
# Переменные окружения
# ------------------------
ENV POETRY_HOME="/opt/poetry" \
    PATH="/opt/poetry/bin:$PATH" \
    PYTHONPATH="/app/src" \
    ENABLE_TRACING="1"

WORKDIR /app

# ------------------------
# Системные зависимости
# ------------------------
RUN apt-get update && apt-get install -y \
    curl wget unzip gcc python3-dev \
    postgresql-client libpq5 \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --with dev

# ------------------------
# Установка Allure Pytest
# ------------------------
RUN poetry add --dev allure-pytest

# ------------------------
# Установка OpenTelemetry
# ------------------------
RUN pip install --no-cache-dir \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation-httpx

# ------------------------
# Копируем весь проект
# ------------------------
COPY . /app

# ------------------------
# Создаем папки для логов, отчетов и профилей
# ------------------------
RUN mkdir -p /app/logs /app/templates /app/static /app/allure-results /app/test-reports /app/profiles

# ------------------------
# Порт приложения
# ------------------------
EXPOSE 8000

# ------------------------
# Команда запуска FastAPI
# ------------------------
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
