# External Service Contract (Lab 7)

## Provider (real mode)

- Base URL: `https://jsonplaceholder.typicode.com`
- Endpoint: `GET /todos/{id}`

## Contract

Request:

- Method: `GET`
- Path param: `id` (`int > 0`)
- Response: `application/json`

Response body (minimal fields):

```json
{
  "userId": 1,
  "id": 1,
  "title": "delectus aut autem",
  "completed": false
}
```

## Mock provider

- Base URL: `http://external-mock:8090`
- Endpoint: `GET /todos/{id}`
- Healthcheck: `GET /health`

The mock server keeps the same response schema as the real provider.

## Application endpoint

Application exposes normalized response via:

- `GET /api/external/todos/{todo_id}`

Example response:

```json
{
  "contract": "jsonplaceholder-todo-v1",
  "source": {
    "mode": "mock",
    "base_url": "http://external-mock:8090",
    "endpoint": "/todos/1"
  },
  "todo": {
    "id": 1,
    "user_id": 9001,
    "title": "mock-todo-1",
    "completed": false
  }
}
```
