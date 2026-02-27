from __future__ import annotations

import logging

from typing import Any
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from logger import setup_logging
from routers.activity import activity_router
from routers.event import event_router
from routers.lodging import lodging_router
from routers.program import program_router
from routers.session import session_router
from routers.user import user_router
from routers.venue import venue_router
from tracing import setup_tracing


templates = Jinja2Templates(directory="templates")

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Запуск приложения")
    yield
    logger.info("Завершение работы приложения")


app = FastAPI(lifespan=lifespan)
setup_tracing(app)
routers = [
    session_router,
    program_router,
    venue_router,
    user_router,
    lodging_router,
    event_router,
    activity_router,
]

for r in routers:
    app.include_router(r)


@app.get("/", response_class=HTMLResponse)
async def serve_main_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("main.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", {"request": request})


@app.exception_handler(Exception)
async def handle_exceptions(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Ошибка при обработке запроса: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "OK"}


@app.get("/api/benchmark/json")
async def benchmark_json_serialization() -> dict[str, str | list[dict[str, str | int]]]:
    """Эндпоинт для бенчмарка сериализации JSON (аналог TechEmpower json test)."""
    return {
        "message": "Hello, World!",
        "items": [
            {"id": i, "name": f"item_{i}", "value": i * 100}
            for i in range(50)
        ],
    }


@app.get("/api/benchmark/medium")
async def benchmark_medium() -> dict[str, list[dict[str, str | int]]]:
    """Средний запрос — JSON ~10KB (эквивалент для сравнения с Flask)."""
    return {
        "venues": [
            {"id": i, "name": f"Venue_{i}", "city": "Moscow", "capacity": 100 + i}
            for i in range(50)
        ],
    }


@app.get("/api/benchmark/heavy")
async def benchmark_heavy() -> dict[str, list[dict[str, Any]]]:
    """Тяжёлый запрос — JSON ~50KB (эквивалент для сравнения с Flask)."""
    return {
        "events": [
            {
                "id": i,
                "name": f"Event_{i}",
                "activities": [{"id": j, "name": f"act_{j}"} for j in range(20)],
                "lodgings": [{"id": k, "name": f"lodg_{k}"} for k in range(5)],
            }
            for i in range(30)
        ],
    }
