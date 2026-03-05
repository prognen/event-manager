from __future__ import annotations

from fastapi import FastAPI
from fastapi import HTTPException


app = FastAPI(title="External Todo Mock", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int) -> dict[str, int | str | bool]:
    if todo_id <= 0:
        raise HTTPException(status_code=400, detail="todo_id must be > 0")

    return {
        "userId": 9000 + todo_id,
        "id": todo_id,
        "title": f"mock-todo-{todo_id}",
        "completed": todo_id % 2 == 0,
    }
