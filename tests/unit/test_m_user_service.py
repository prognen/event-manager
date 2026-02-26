from __future__ import annotations

import re

from unittest.mock import AsyncMock
from unittest.mock import Mock

import bcrypt
import pytest

from models.user import User
from repository.user_repository import UserRepository
from services.user_service import AuthService
from services.user_service import UserService


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_service_should_registrate_user() -> None:
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1234567890",
        phone_number="89261111111",
        email="nl@ii.info",
        login="proGsa",
        password="1234D!f333",
    )
    repo = Mock(spec=UserRepository, autospec=True)
    repo.add = AsyncMock(return_value=user)

    auth = AuthService(repo)
    result = await auth.registrate(user)

    assert result.login == "proGsa"
    repo.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_registrate_failure_duplicate() -> None:
    user = User(
        user_id=1,
        fio="Test",
        number_passport="1266449003",
        phone_number="89098866123",
        email="t@t.com",
        login="login",
        password="pas!11fdfDAs",
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.add = AsyncMock(side_effect=Exception("duplicate"))

    auth = AuthService(repo)
    with pytest.raises(
        ValueError, match=re.escape("Пользователь с таким логином уже существует")
    ):
        await auth.registrate(user)


@pytest.mark.asyncio
async def test_service_should_successfull_delete_existed_user() -> None:
    repo = Mock(spec=UserRepository, autospec=True)
    repo.delete = AsyncMock(return_value=None)

    service = UserService(repo)
    await service.delete(1)

    repo.delete.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_delete_not_existed_user() -> None:
    repo = Mock(spec=UserRepository, autospec=True)
    repo.delete = AsyncMock(side_effect=Exception("not found"))

    service = UserService(repo)
    with pytest.raises(ValueError, match=re.escape("Пользователь не найден.")):
        await service.delete(122)


@pytest.mark.asyncio
async def test_should_succesfull_get_existed_user_by_id() -> None:
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1234567890",
        phone_number="89261111111",
        email="nl@ii.info",
        login="proGsa",
        password="1234D!f333",
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.get_by_id = AsyncMock(return_value=user)

    service = UserService(repo)
    result = await service.get_by_id(1)

    assert result == user
    repo.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_get_not_existed_user() -> None:
    repo = Mock(spec=UserRepository, autospec=True)
    repo.get_by_id = AsyncMock(return_value=None)

    service = UserService(repo)
    result = await service.get_by_id(999)

    assert result is None
    repo.get_by_id.assert_awaited_once_with(999)


@pytest.mark.asyncio
async def test_get_list_success() -> None:
    users = [
        User(
            user_id=1,
            fio="U1",
            number_passport="1000888896",
            phone_number="89961294321",
            email="1@test.com",
            login="u1",
            password="padaAQD11!1",
        )
    ]
    repo = Mock(spec=UserRepository, autospec=True)
    repo.get_list = AsyncMock(return_value=users)

    service = UserService(repo)
    result = await service.get_list()

    assert result == users
    repo.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_list_failure() -> None:
    repo = Mock(spec=UserRepository, autospec=True)
    repo.get_list = AsyncMock(side_effect=Exception("db error"))

    service = UserService(repo)
    with pytest.raises(Exception, match="db error"):
        await service.get_list()


@pytest.mark.asyncio
async def test_should_succesfull_update_existed_user_by_id() -> None:
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1234567890",
        phone_number="89261111111",
        email="nl@ii.info",
        login="proGsa",
        password="1234D!f333",
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.update = AsyncMock(return_value=user)

    service = UserService(repo)
    result = await service.update(user)

    assert result == user
    repo.update.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_update_not_existed_user() -> None:
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1234567890",
        phone_number="89261111111",
        email="nl@ii.info",
        login="proGsa",
        password="1234D!f333",
    )
    repo = Mock(spec=UserRepository, autospec=True)
    repo.update = AsyncMock(side_effect=Exception("not found"))

    service = UserService(repo)
    with pytest.raises(ValueError, match=re.escape("Пользователь не найден.")):
        await service.update(user)


@pytest.mark.asyncio
async def test_should_succesfull_login_existed_user_with_right_password() -> None:
    password = "secre!Se@t123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1234567890",
        phone_number="89261111111",
        email="nl@ii.info",
        login="proGsa",
        password=hashed,
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.get_by_login = AsyncMock(return_value=user)

    auth = AuthService(repo)
    result = await auth.authenticate("user", password)

    assert result == user
    repo.get_by_login.assert_awaited_once_with("user")


@pytest.mark.asyncio
async def test_should_succesfull_login_existed_user_with_wrong_password() -> None:
    password = "secret123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1234567890",
        phone_number="89261111111",
        email="nl@ii.info",
        login="proGsa",
        password=hashed,
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.get_by_login = AsyncMock(return_value=user)

    auth = AuthService(repo)
    result = await auth.authenticate("user", "wrongpass")

    assert result is None


@pytest.mark.asyncio
async def test_verify_password_and_hash() -> None:
    password = "test1234!"
    hashed = AuthService.get_password_hash(password)

    assert AuthService.verify_password(password, hashed)
    assert not AuthService.verify_password("wrong", hashed)


@pytest.mark.asyncio
async def test_jwt_token_cycle() -> None:
    user = User(
        user_id=42,
        fio="U",
        number_passport="1111111111",
        phone_number="89110223813",
        email="u@u.com",
        login="user",
        password="pada!!!d2ekS",
        is_admin=True,
    )

    token = AuthService.create_access_token(user)
    decoded = AuthService.decode_token(token)

    assert decoded["sub"] == "42"
    assert decoded["login"] == "user"
    assert decoded["is_admin"] is True


@pytest.mark.asyncio
async def test_add_user_success() -> None:
    user = User(
        user_id=1,
        fio="Test",
        number_passport="1234567890",
        phone_number="89111111111",
        email="test@test.com",
        login="login",
        password="pD!D12edaass",
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.add = AsyncMock(return_value=user)

    service = UserService(repo)
    result = await service.add(user)

    assert result == user
    repo.add.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_add_user_failure_duplicate() -> None:
    user = User(
        user_id=1,
        fio="Test",
        number_passport="1234567890",
        phone_number="89111111111",
        email="test@test.com",
        login="login",
        password="pa!22ksOAsss",
    )

    repo = Mock(spec=UserRepository, autospec=True)
    repo.add = AsyncMock(side_effect=Exception("duplicate"))

    service = UserService(repo)
    with pytest.raises(
        ValueError, match=re.escape("Администратор c таким ID уже существует.")
    ):
        await service.add(user)



