from __future__ import annotations

import logging

from typing import Any
from typing import Literal

import httpx

from fastapi import HTTPException

from settings import settings


logger = logging.getLogger(__name__)

ServiceMode = Literal["mock", "real"]


class ExternalTodoService:
    @staticmethod
    def _get_mode() -> ServiceMode:
        mode = settings.EXTERNAL_SERVICE_MODE.strip().lower()
        if mode == "mock":
            return "mock"
        if mode == "real":
            return "real"
        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid EXTERNAL_SERVICE_MODE. "
                "Expected 'mock' or 'real'."
            ),
        )

    @staticmethod
    def _get_base_url(mode: ServiceMode) -> str:
        if mode == "mock":
            return settings.EXTERNAL_SERVICE_MOCK_BASE_URL.rstrip("/")
        return settings.EXTERNAL_SERVICE_REAL_BASE_URL.rstrip("/")

    async def get_todo(self, todo_id: int) -> dict[str, Any]:
        if todo_id <= 0:
            raise HTTPException(status_code=400, detail="todo_id must be > 0")

        mode = self._get_mode()
        base_url = self._get_base_url(mode)
        url = f"{base_url}/todos/{todo_id}"

        try:
            async with httpx.AsyncClient(
                timeout=settings.EXTERNAL_SERVICE_TIMEOUT_SEC
            ) as client:
                response = await client.get(url, headers={"accept": "application/json"})
        except httpx.HTTPError as exc:
            logger.error("External service request failed: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="Failed to reach external service",
            ) from exc

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="External todo not found")
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=(
                    "External service returned error "
                    f"status={response.status_code}"
                ),
            )

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("External service returned non-JSON payload")
            raise HTTPException(
                status_code=502,
                detail="External service returned invalid JSON",
            ) from exc

        return {
            "contract": "jsonplaceholder-todo-v1",
            "source": {
                "mode": mode,
                "base_url": base_url,
                "endpoint": f"/todos/{todo_id}",
            },
            "todo": {
                "id": int(payload.get("id", todo_id)),
                "user_id": int(payload.get("userId", 0)),
                "title": str(payload.get("title", "")),
                "completed": bool(payload.get("completed", False)),
            },
        }
