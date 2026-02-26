import uuid
import pytest
import requests
from pytest_bdd import scenarios, given, when, then
from main import app
from models.user import User
from faker import Faker
import os

fake = Faker("ru_RU")
BDD_PASS = os.environ.get("BDD_USER_PASS", "Test@Pass123")

scenarios("../features/login_limit.feature")

BASE_URL = "http://localhost:8000"


@pytest.fixture
def test_user():
    uid = uuid.uuid4().hex[:8]
    login = f"techuser_limit_{uid}"
    password = BDD_PASS
    email = f"testuser_{uid}@test.com"
    phone = "80261940112"

    user = User(
        user_id=1,
        fio=fake.name(),
        number_passport=uid + uid[:2],
        phone_number=phone,
        email=email,
        login=login,
        password=password,
        is_admin=False,
    )

    # Регистрация пользователя
    resp = requests.post(f"{BASE_URL}/api/register", json=user.model_dump())
    resp.raise_for_status()
    data = resp.json()
    user_data = {
        "login": login,
        "password": password,
        "user_id": data["user_id"],
        "token": data["access_token"],
    }

    yield user_data

    # Удаление пользователя после теста
    requests.delete(
        f"{BASE_URL}/api/delete/{data['user_id']}",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )


@given("тестовый пользователь создан")
def given_user(test_user):
    return test_user


@when("пользователь 5 раз вводит неверный пароль")
def when_wrong_password(test_user):
    login = test_user["login"]

    for _ in range(5):
        resp = requests.post(
            f"{BASE_URL}/api/login1", json={"login": login, "password": "wrongpass"}
        )
        assert resp.status_code == 401  # Unauthorized


@then("система блокирует дальнейший вход")
def then_blocked_login(test_user):
    login = test_user["login"]
    password = test_user["password"]

    resp = requests.post(
        f"{BASE_URL}/api/login1", json={"login": login, "password": password}
    )
    assert resp.status_code == 403  # Forbidden / блокировка



