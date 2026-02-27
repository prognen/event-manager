"""Минимальное Flask-приложение для сравнения с FastAPI (Лабораторная №3)."""
from __future__ import annotations

import os

import bcrypt
import psycopg2
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://egor:egor@localhost:5438/mydb"
)


@app.route("/health")
def health() -> dict:
    return {"status": "OK"}


@app.route("/api/benchmark/json")
def benchmark_json() -> dict:
    """Эквивалент FastAPI /api/benchmark/json."""
    return {
        "message": "Hello, World!",
        "items": [{"id": i, "name": f"item_{i}", "value": i * 100} for i in range(50)],
    }


@app.route("/api/benchmark/medium")
def benchmark_medium() -> dict:
    """Средний запрос — JSON ~10KB (эквивалент /venue.html по объёму)."""
    return {
        "venues": [
            {"id": i, "name": f"Venue_{i}", "city": "Moscow", "capacity": 100 + i}
            for i in range(50)
        ],
    }


@app.route("/api/benchmark/heavy")
def benchmark_heavy() -> dict:
    """Тяжёлый запрос — JSON ~50KB (эквивалент /event.html)."""
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


def _get_user_by_login(login: str) -> tuple[int, str] | None:
    """Возвращает (user_id, password_hash) или None."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, password FROM event_db.users WHERE login = %s",
                    (login,),
                )
                row = cur.fetchone()
                if row:
                    return (row[0], row[1])
    except Exception:
        pass
    return None


@app.route("/api/login", methods=["POST"])
def login() -> tuple[dict, int]:
    """Реальный логин: БД + bcrypt (честное сравнение с FastAPI)."""
    data = request.get_json() or {}
    login_val = data.get("login")
    password_val = data.get("password")
    if not login_val or not password_val:
        return jsonify({"detail": "Invalid credentials"}), 401

    user = _get_user_by_login(login_val)
    if not user:
        return jsonify({"detail": "Invalid credentials"}), 401

    user_id, password_hash = user
    try:
        if not bcrypt.checkpw(
            password_val.encode("utf-8"), password_hash.encode("utf-8")
        ):
            return jsonify({"detail": "Invalid credentials"}), 401
    except Exception:
        return jsonify({"detail": "Invalid credentials"}), 401

    return jsonify({"access_token": "token", "user_id": user_id}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
