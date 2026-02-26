from __future__ import annotations

import os
import uuid

import allure
import httpx
import pytest

from faker import Faker


fake = Faker("ru_RU")

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


@allure.feature("MVP: Управление мероприятиями")
@allure.story("Полный MVP-сценарий: регистрация → вход → создание мероприятия → просмотр")
class TestMVPEventManagementFlow:
    """MVP-сценарий организатора мероприятий.

    Демонстрирует ключевой функционал системы:
    1. Регистрация нового пользователя
    2. Вход в систему
    3. Просмотр справочников (площадки, активности, размещения, маршруты)
    4. Создание мероприятия с маршрутом через /session/new
    5. Проверка появления мероприятия в системе
    6. Просмотр профиля с активными мероприятиями
    """

    @pytest.mark.asyncio
    async def test_full_event_management_scenario(self) -> None:
        uid = uuid.uuid4().hex[:8]
        user_login = f"mvp_test_{uid}"
        user_password = "Test@Pass123"
        user_email = f"mvp_test_{uid}@test.com"
        user_phone = f"8926{uuid.uuid4().int % 10_000_000:07d}"

        async with httpx.AsyncClient(
            base_url=BASE_URL, follow_redirects=True, timeout=30.0
        ) as client:
            user_id: int | None = None
            token: str | None = None

            try:
                # ---- ARRANGE ----
                with allure.step("Шаг 1: Регистрация нового пользователя"):
                    register_payload = {
                        "fio": fake.name(),
                        "number_passport": uid + uid[:2],
                        "phone_number": user_phone,
                        "email": user_email,
                        "login": user_login,
                        "password": user_password,
                        "is_admin": False,
                    }
                    resp = await client.post("/api/register", json=register_payload)
                    assert resp.status_code == 200, (
                        f"Ошибка регистрации (HTTP {resp.status_code}): {resp.text}"
                    )
                    reg_data = resp.json()
                    user_id = reg_data["user_id"]
                    token = reg_data["access_token"]
                    assert user_id is not None, "user_id не получен после регистрации"
                    assert token, "access_token не получен после регистрации"

                headers = {"Authorization": f"Bearer {token}"}

                # ---- ACT: вход ----
                with allure.step("Шаг 2: Аутентификация (прямой вход /api/login)"):
                    login_resp = await client.post(
                        "/api/login",
                        json={"login": user_login, "password": user_password},
                    )
                    assert login_resp.status_code == 200, (
                        f"Вход не выполнен (HTTP {login_resp.status_code}): {login_resp.text}"
                    )
                    login_data = login_resp.json()

                # ---- ASSERT: вход ----
                with allure.step("Проверка токена после входа"):
                    assert "access_token" in login_data, "Токен не получен после входа"
                    assert login_data.get("user_login") == user_login

                # ---- ACT: просмотр справочников ----
                with allure.step("Шаг 3: Просмотр доступных площадок"):
                    venues_resp = await client.get("/venue.html")
                    assert venues_resp.status_code == 200

                with allure.step("Проверка наличия площадок в системе"):
                    assert "Москва" in venues_resp.text, "Площадка 'Москва' не найдена"
                    assert "Воронеж" in venues_resp.text, "Площадка 'Воронеж' не найдена"

                with allure.step("Шаг 4: Просмотр активностей на площадках"):
                    activities_resp = await client.get("/activity.html")
                    assert activities_resp.status_code == 200

                with allure.step("Проверка наличия активностей"):
                    assert "Конференция" in activities_resp.text, (
                        "Активность 'Конференция' не найдена"
                    )

                with allure.step("Шаг 5: Просмотр вариантов размещения"):
                    lodgings_resp = await client.get("/lodging.html")
                    assert lodgings_resp.status_code == 200

                with allure.step("Проверка наличия размещений"):
                    assert "Мир" in lodgings_resp.text, "Размещение 'Мир' не найдено"

                with allure.step("Шаг 6: Просмотр доступных маршрутов (программ)"):
                    programs_resp = await client.get("/program.html")
                    assert programs_resp.status_code == 200

                with allure.step("Проверка наличия маршрутов"):
                    assert "Автомобиль" in programs_resp.text, (
                        "Маршруты типа 'Автомобиль' не найдены"
                    )

                # ---- ACT: создание мероприятия ----
                with allure.step(
                    "Шаг 7: Создание мероприятия с маршрутом Москва → Воронеж"
                ):
                    session_payload = {
                        "from_venue": "1",
                        "to_venue": "2",
                        "transport": "Автомобиль",
                        "start_date": "05.05.2026",
                        "end_date": "08.05.2026",
                        "user_id": str(user_id),
                        "activities[]": ["1"],
                        "lodgings[]": ["1"],
                    }
                    session_resp = await client.post(
                        "/session/new", json=session_payload, headers=headers
                    )
                    assert session_resp.status_code == 200, (
                        f"Ошибка создания сессии (HTTP {session_resp.status_code}): "
                        f"{session_resp.text}"
                    )
                    session_result = session_resp.json()

                # ---- ASSERT: мероприятие создано ----
                with allure.step("Проверка ответа от /session/new"):
                    assert "session_id" in session_result, (
                        "session_id не получен в ответе"
                    )
                    assert "program_id" in session_result, (
                        "program_id не получен в ответе"
                    )
                    session_id = session_result["session_id"]
                    assert session_id > 0, "session_id должен быть положительным числом"

                with allure.step("Шаг 8: Проверка — мероприятие появилось в системе"):
                    events_resp = await client.get("/event.html")
                    assert events_resp.status_code == 200
                    assert "Активное" in events_resp.text, (
                        "Активное мероприятие не отображается на странице мероприятий"
                    )

                with allure.step("Шаг 9: Проверка — сессия появилась в системе"):
                    sessions_resp = await client.get("/session.html")
                    assert sessions_resp.status_code == 200

                with allure.step(
                    "Шаг 10: Просмотр профиля пользователя с активными мероприятиями"
                ):
                    profile_resp = await client.get(f"/profile_user/{user_id}")
                    assert profile_resp.status_code == 200

            finally:
                # ---- TEARDOWN ----
                if user_id is not None and token is not None:
                    with allure.step("Очистка: удаление тестового пользователя"):
                        await client.delete(
                            f"/api/delete/{user_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )
