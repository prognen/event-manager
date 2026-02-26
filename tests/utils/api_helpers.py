from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from main import app

BASE_URL = "http://localhost:8000"


async def api_post(url, json=None, headers=None):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        return await client.post(url, json=json, headers=headers)


async def api_delete(url, headers=None):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        return await client.delete(url, headers=headers)



