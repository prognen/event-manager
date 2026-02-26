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
BASE_URL = "http://localhost:8000"

scenarios("../features/password_rotation.feature")


# ------------------------------
# Фикстура для пользователя со старым паролем
# ------------------------------
@pytest.fixture
def password_user():
    login = f"techuser_oldpass_{uuid.uuid4().hex[:8]}"
    old_password = BDD_PASS
    email = fake.email()
    phone = "89259930123"

    user = User(
        user_id=1,
        fio=fake.name(),
        number_passport=str(fake.ssn()),
        phone_number=phone,
        email=email,
        login=login,
        password=old_password,
        is_admin=False,
    )

    # Регистрация пользователя
    resp = requests.post(f"{BASE_URL}/api/register", json=user.model_dump())
    resp.raise_for_status()
    data = resp.json()

    user_data = {
        "login": login,
        "old_password": old_password,
        "user_id": data["user_id"],
        "token": data["access_token"],
    }

    yield user_data

    # Удаляем пользователя после теста
    requests.delete(
        f"{BASE_URL}/api/delete/{data['user_id']}",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )


# ------------------------------
# Step Definitions
# ------------------------------


@given("тестовый пользователь со старым паролем создан")
def given_user(password_user):
    return password_user


@given("срок действия пароля истёк")
def given_password_expired(password_user):
    resp = requests.post(
        f"{BASE_URL}/api/expire-password", json={"login": password_user["login"]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("expired") is True

    password_user["expired"] = True
    return password_user


@when("пользователь входит со старым паролем")
def when_login_old_password(password_user):
    resp = requests.post(
        f"{BASE_URL}/api/login1",
        json={
            "login": password_user["login"],
            "password": password_user["old_password"],
        },
    )
    password_user["login_resp"] = resp
    assert resp.status_code == 403  # сервер должен блокировать вход при истёкшем пароле


@then("система требует сменить пароль")
def then_require_change(password_user):
    resp = password_user["login_resp"]
    data = resp.json()
    assert "password_expired" in data  # сервер возвращает поле password_expired


@when("пользователь вводит новый пароль")
def when_enter_new_password(password_user):
    new_password = "NewPass123!"
    password_user["new_password"] = new_password
    resp = requests.post(
        f"{BASE_URL}/api/change-password",
        json={"login": password_user["login"], "new_password": new_password},
    )
    assert resp.status_code == 200


@then("система принимает новый пароль")
def then_accept_new_password(password_user):
    assert "new_password" in password_user


@then("вход с новым паролем проходит успешно")
def then_login_new_password(password_user):
    resp = requests.post(
        f"{BASE_URL}/api/login1",
        json={
            "login": password_user["login"],
            "password": password_user["new_password"],
        },
    )
    assert resp.status_code == 200


@then("вход со старым паролем невозможен")
def then_login_old_password_fail(password_user):
    resp = requests.post(
        f"{BASE_URL}/api/login1",
        json={
            "login": password_user["login"],
            "password": password_user["old_password"],
        },
    )
    assert resp.status_code == 401



