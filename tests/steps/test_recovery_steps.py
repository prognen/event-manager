import pytest
from pytest_bdd import scenarios, given, when, then
import requests
from main import app
from models.user import User
from faker import Faker
import os

fake = Faker("ru_RU")

scenarios("../features/recovery.feature")
BDD_PASS = os.environ.get("BDD_USER_PASS")
# BDD_PASS = "Test123!"
BASE_URL = "http://localhost:8000"


# ------------------------------
# Синхронная фикстура пользователя
# ------------------------------
@pytest.fixture
def recover_user():
    login = "techuser_block"
    password = BDD_PASS
    email = fake.email()
    phone = "89255930166"

    user = User(
        user_id=1,
        fio=fake.name(),
        number_passport=str(fake.ssn()),
        phone_number=phone,
        email=email,
        login=login,
        password=password,
        is_admin=False,
    )

    resp = requests.post(f"{BASE_URL}/api/register", json=user.model_dump())
    data = resp.json()
    user_data = {
        "login": login,
        "password": password,
        "user_id": data["user_id"],
        "token": data["access_token"],
    }

    yield user_data

    requests.delete(
        f"{BASE_URL}/api/delete/{data['user_id']}",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )


# ------------------------------
# Шаги BDD
# ------------------------------
@given("тестовый пользователь создан для восстановления")
def given_user(recover_user):
    return recover_user


@when("пользователь 5 раз вводит неверный пароль")
def when_wrong_password(recover_user):
    login = recover_user["login"]

    for _ in range(5):
        resp = requests.post(
            f"{BASE_URL}/api/login1", json={"login": login, "password": "wrongpass"}
        )
        assert resp.status_code == 401


@when("система блокирует учетную запись")
def when_blocked(recover_user):
    login = recover_user["login"]
    password = recover_user["password"]

    resp_blocked = requests.post(
        f"{BASE_URL}/api/login1", json={"login": login, "password": password}
    )
    assert resp_blocked.status_code == 403


@when("пользователь запрашивает восстановление пароля")
def when_recover_password(recover_user):
    login = recover_user["login"]

    recover_resp = requests.post(
        f"{BASE_URL}/api/recover-password", json={"login": login}
    )
    assert recover_resp.status_code == 200


@then("система позволяет снова войти")
def then_can_login(recover_user):
    login = recover_user["login"]
    password = recover_user["password"]

    resp_login = requests.post(
        f"{BASE_URL}/api/login1", json={"login": login, "password": password}
    )
    assert resp_login.status_code == 200



