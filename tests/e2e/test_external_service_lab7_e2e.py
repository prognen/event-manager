from __future__ import annotations

import os

import httpx
import pytest


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
EXTERNAL_TEST_MODE = os.environ.get("EXTERNAL_TEST_MODE", "none").strip().lower()


@pytest.mark.asyncio
async def test_external_service_integration_mock_mode() -> None:
    if EXTERNAL_TEST_MODE != "mock":
        pytest.skip("mock-mode test is disabled for this run")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
        response = await client.get("/api/external/todos/1")

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["contract"] == "jsonplaceholder-todo-v1"
    assert payload["source"]["mode"] == "mock"
    assert payload["todo"]["id"] == 1
    assert payload["todo"]["title"]
    assert isinstance(payload["todo"]["completed"], bool)


@pytest.mark.asyncio
async def test_external_service_integration_real_mode() -> None:
    if EXTERNAL_TEST_MODE != "real":
        pytest.skip("real-mode test is disabled for this run")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
        response = await client.get("/api/external/todos/1")

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["contract"] == "jsonplaceholder-todo-v1"
    assert payload["source"]["mode"] == "real"
    assert payload["todo"]["id"] == 1
    assert payload["todo"]["title"]
    assert isinstance(payload["todo"]["completed"], bool)
