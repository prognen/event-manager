from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from services.external_todo_service import ExternalTodoService


external_service_router = APIRouter()

_external_todo_service = ExternalTodoService()


@external_service_router.get("/api/external/todos/{todo_id}")
async def get_external_todo(todo_id: int) -> dict[str, Any]:
    return await _external_todo_service.get_todo(todo_id)
