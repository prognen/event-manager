from __future__ import annotations

import re

from datetime import datetime
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from models.session import Session
from repository.session_repository import SessionRepository
from services.session_service import SessionService


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_should_successfull_get_session_by_id() -> None:
    session = Session(
        session_id=1,
        program=None,
        event=None,
        start_time=datetime(2025, 1, 1, 12, 0, 0),
        end_time=datetime(2025, 1, 2, 12, 0, 0),
        type="Личные",
    )
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.get_by_id = AsyncMock(return_value=session)

    service = SessionService(repo)
    result = await service.get_by_id(1)

    assert result == session
    repo.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_should_throw_exception_when_get_by_id_fails() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.get_by_id = AsyncMock(side_effect=ValueError)

    service = SessionService(repo)
    with pytest.raises(ValueError):
        await service.get_by_id(123)


@pytest.mark.asyncio
async def test_should_successfull_get_all_sessions() -> None:
    sessions = [
        Session(
            session_id=1,
            program=None,
            event=None,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 3, 12, 0, 0),
            type="Личные",
        )
    ]
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.get_list = AsyncMock(return_value=sessions)

    service = SessionService(repo)
    result = await service.get_all_sessions()

    assert result == sessions
    repo.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_successfull_add_session() -> None:
    session = Session(
        session_id=1,
        program=None,
        event=None,
        start_time=datetime(2025, 1, 1, 12, 0, 0),
        end_time=datetime(2025, 1, 3, 12, 0, 0),
        type="Личные",
    )
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.add = AsyncMock(return_value=session)

    service = SessionService(repo)
    result = await service.add(session)

    assert result == session
    repo.add.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_should_throw_exception_at_add_duplicate() -> None:
    session = Session(
        session_id=1,
        program=None,
        event=None,
        start_time=datetime(2025, 1, 1, 12, 0, 0),
        end_time=datetime(2025, 1, 3, 12, 0, 0),
        type="Личные",
    )
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.add = AsyncMock(side_effect=Exception)

    service = SessionService(repo)
    with pytest.raises(
        ValueError, match=re.escape("Сессия c таким ID уже существует.")
    ):
        await service.add(session)


@pytest.mark.asyncio
async def test_should_successfull_update_session() -> None:
    session = Session(
        session_id=1,
        program=None,
        event=None,
        start_time=datetime(2025, 1, 1, 12, 0, 0),
        end_time=datetime(2025, 1, 3, 12, 0, 0),
        type="Личные",
    )
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.update = AsyncMock(return_value=None)

    service = SessionService(repo)
    result = await service.update(session)

    assert result == session
    repo.update.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_should_throw_exception_at_update_not_existed() -> None:
    session = Session(
        session_id=1,
        program=None,
        event=None,
        start_time=datetime(2025, 1, 1, 12, 0, 0),
        end_time=datetime(2025, 1, 3, 12, 0, 0),
        type="Личные",
    )
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.update = AsyncMock(side_effect=Exception)

    service = SessionService(repo)
    with pytest.raises(ValueError, match=re.escape("Сессия не найдена.")):
        await service.update(session)


@pytest.mark.asyncio
async def test_should_successfull_delete_session() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.delete = AsyncMock(return_value=None)

    service = SessionService(repo)
    await service.delete(1)

    repo.delete.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_should_throw_exception_at_delete_not_existed() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.delete = AsyncMock(side_effect=Exception)

    service = SessionService(repo)
    with pytest.raises(ValueError, match=re.escape("Сессия не найдена.")):
        await service.delete(1)


@pytest.mark.asyncio
async def test_should_successfull_insert_venue_after() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.insert_venue_after = AsyncMock(return_value=None)

    service = SessionService(repo)
    await service.insert_venue_after(1, 2, 3, "Автобус")

    repo.insert_venue_after.assert_awaited_once_with(1, 2, 3, "Автобус")


@pytest.mark.asyncio
async def test_should_throw_exception_at_insert_venue_after() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.insert_venue_after = AsyncMock(side_effect=Exception)

    service = SessionService(repo)
    with pytest.raises(ValueError, match=re.escape("Площадку не получилось добавить.")):
        await service.insert_venue_after(1, 2, 3, "Автобус")


@pytest.mark.asyncio
async def test_should_successfull_delete_venue_from_session() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.delete_venue_from_session = AsyncMock(return_value=None)

    service = SessionService(repo)
    await service.delete_venue_from_session(1, 2)

    repo.delete_venue_from_session.assert_awaited_once_with(1, 2)


@pytest.mark.asyncio
async def test_should_throw_exception_at_delete_venue_from_session() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.delete_venue_from_session = AsyncMock(side_effect=Exception)

    service = SessionService(repo)
    with pytest.raises(
        ValueError, match=re.escape("Площадку не получилось удалить из сессии.")
    ):
        await service.delete_venue_from_session(1, 2)


@pytest.mark.asyncio
async def test_should_successfull_change_transport() -> None:
    session = Session(
        session_id=1,
        program=None,
        event=None,
        start_time=datetime(2025, 1, 1, 12, 0, 0),
        end_time=datetime(2025, 1, 3, 12, 0, 0),
        type="Личные",
    )
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.change_transport = AsyncMock(return_value=session)

    service = SessionService(repo)
    result = await service.change_transport(1, 1, "Поезд")

    assert result == session
    repo.change_transport.assert_awaited_once_with(1, 1, "Поезд")


@pytest.mark.asyncio
async def test_should_throw_exception_at_change_transport() -> None:
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.change_transport = AsyncMock(side_effect=Exception)

    service = SessionService(repo)
    with pytest.raises(
        ValueError, match=re.escape("Не удалось изменить транспорт в сессии.")
    ):
        await service.change_transport(1, 1, "Поезд")


@pytest.mark.asyncio
async def test_should_successfull_get_sessions_by_user_and_status_and_type() -> None:
    sessions = [
        Session(
            session_id=1,
            program=None,
            event=None,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 3, 12, 0, 0),
            type="Личные",
        )
    ]
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.get_sessions_by_user_and_status_and_type = AsyncMock(return_value=sessions)

    service = SessionService(repo)
    result = await service.get_sessions_by_user_and_status_and_type(1, "Активное", "Личные")

    assert result == sessions
    repo.get_sessions_by_user_and_status_and_type.assert_awaited_once_with(
        1, "Активное", "Личные"
    )


@pytest.mark.asyncio
async def test_should_successfull_get_sessions_by_type() -> None:
    sessions = [
        Session(
            session_id=2,
            program=None,
            event=None,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 3, 12, 0, 0),
            type="Личные",
        )
    ]
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.get_sessions_by_type = AsyncMock(return_value=sessions)

    service = SessionService(repo)
    result = await service.get_sessions_by_type("Личные")

    assert result == sessions
    repo.get_sessions_by_type.assert_awaited_once_with("Личные")


@pytest.mark.asyncio
async def test_should_successfull_get_session_parts() -> None:
    parts = [{"venue": "Москва"}]
    repo = Mock(spec=SessionRepository, autospec=True)
    repo.get_session_parts = AsyncMock(return_value=parts)

    service = SessionService(repo)
    result = await service.get_session_parts(1)

    assert result == parts
    repo.get_session_parts.assert_awaited_once_with(1)
