import re
import base64
import pytest
import requests
from pytest_bdd import scenarios, given, when, then
from main import app  # для работы с ASGITransport не нужно, т.к. синхронно
from models.user import User
from faker import Faker
import os

fake = Faker("ru_RU")

scenarios("../features/authentication.feature")

BDD_PASS = os.environ.get("BDD_USER_PASS")
# BDD_PASS = "Test123!"


# ------------------------------
# Синхронная фикстура для тестового пользователя
# ------------------------------
@pytest.fixture
def test_user_2fa():
    login = "techuser_2fa"
    password = BDD_PASS
    email = fake.email()
    phone = "89261930112"

    # Создаём payload для регистрации
    user_payload = {
        "fio": fake.name(),
        "number_passport": str(fake.ssn()),
        "phone_number": phone,
        "email": email,
        "login": login,
        "password": password,
        "is_admin": False,
    }

    # Регистрация пользователя
    resp = requests.post("http://localhost:8000/api/register", json=user_payload)
    resp.raise_for_status()  # выбросим исключение, если код != 2xx
    data = resp.json()

    user_data = {
        "login": login,
        "password": password,
        "user_id": data["user_id"],
        "token": data["access_token"],
    }

    yield user_data

    # Удаляем пользователя после теста
    requests.delete(
        f"http://localhost:8000/api/delete/{data['user_id']}",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )


# ------------------------------
# Шаги BDD (синхронные)
# ------------------------------
@given("существует тестовый пользователь для 2FA")
def given_user(test_user_2fa):
    return test_user_2fa


@when("пользователь выполняет первичный вход")
def when_login(test_user_2fa):
    login = test_user_2fa["login"]
    password = test_user_2fa["password"]

    resp = requests.post(
        "http://localhost:8000/api/login1", json={"login": login, "password": password}
    )
    assert resp.status_code == 200
    test_user_2fa["login_resp"] = resp


@then("на почту отправлен код 2FA")
def then_email_code(test_user_2fa):
    import requests

    # Получаем все письма
    resp = requests.get("http://localhost:8025/api/v2/messages")
    items = resp.json().get("items", [])
    assert len(items) > 0, "Письма не найдены в MailHog"

    last_email = items[0]

    body_b64 = last_email["Content"].get("Body") or last_email.get("Source", "")
    assert body_b64, "Тело письма пустое"

    body = base64.b64decode(body_b64).decode("utf-8", errors="ignore")
    match = re.search(r"Ваш код:\s*(\d{6})", body)
    assert match is not None, f"2FA код не найден в письме. Body:\n{body}"

    code = match.group(1)
    test_user_2fa["2fa_code"] = code


@when("пользователь вводит правильный код")
def when_enter_code(test_user_2fa):
    login = test_user_2fa["login"]
    code = test_user_2fa["2fa_code"]

    resp = requests.post(
        "http://localhost:8000/api/login2", json={"login": login, "code": code}
    )
    test_user_2fa["2fa_resp"] = resp


@then("система выдает действительный access_token")
def then_access_token(test_user_2fa):
    resp = test_user_2fa["2fa_resp"]
    assert resp.status_code == 200
    assert "access_token" in resp.json()



