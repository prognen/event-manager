from __future__ import annotations

import re

from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from abstract_repository.ievent_repository import IEventRepository
from models.lodging import Lodging
from models.activity import Activity
from models.event import Event
from models.user import User
from services.event_service import EventService


TWO = 2
pytestmark = pytest.mark.unit


def create_test_event(event_id: int = 1) -> Event:
    lodging = Lodging(
        lodging_id=1,
        price=20000,
        address="Улица Гоголя, 12",
        name="Four Seasons",
        type="Отель",
        rating=5,
        check_in=datetime(2023, 10, 10, 10, 0, 0),
        check_out=datetime(2023, 10, 10, 18, 0, 0),
    )

    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )

    return Event(
        event_id=event_id,
        status="Активное",
        users=[create_test_user()],
        activities=[activity],
        lodgings=[lodging],
    )


def create_test_user(user_id: int = 1) -> User:
    return User(
        user_id=user_id,
        fio="Test User",
        number_passport="1234567890",
        phone_number="89256482340",
        email="test@example.com",
        login="adkakfsne",
        password="password123!Q",
    )


def create_mock_repository() -> IEventRepository:
    mock_repo = AsyncMock(spec=IEventRepository, autospec=True)

    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_list = AsyncMock()
    mock_repo.add = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.delete = AsyncMock()
    mock_repo.search = AsyncMock()
    mock_repo.complete = AsyncMock()
    mock_repo.get_users_by_event = AsyncMock()
    mock_repo.get_activities_by_event = AsyncMock()
    mock_repo.get_lodgings_by_event = AsyncMock()
    mock_repo.link_activities = AsyncMock()
    mock_repo.link_users = AsyncMock()
    mock_repo.link_lodgings = AsyncMock()
    mock_repo.get_events_for_user = AsyncMock()
    mock_repo.get_event_by_session_id = AsyncMock()

    return cast(IEventRepository, mock_repo)


@pytest.mark.asyncio
async def test_get_by_id_not_found() -> None:
    with patch.object(EventService, "__init__", return_value=None):
        mock_repo = create_mock_repository()
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_by_id.return_value = None

        result = await service.get_by_id(999)

        service.repository.get_by_id.assert_called_once_with(999)
        assert result is None


@pytest.mark.asyncio
async def test_get_all_events_success() -> None:
    test_events = [create_test_event(1), create_test_event(2)]

    with patch.object(EventService, "__init__", return_value=None):
        mock_repo = create_mock_repository()
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_list.return_value = test_events

        result = await service.get_all_events()

        service.repository.get_list.assert_called_once()
        assert result == test_events
        assert len(result) == TWO


@pytest.mark.asyncio
async def test_get_all_events_empty() -> None:
    with patch.object(EventService, "__init__", return_value=None):
        mock_repo = create_mock_repository()
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_list.return_value = []

        result = await service.get_all_events()

        service.repository.get_list.assert_called_once()
        assert result == []
        assert len(result) == 0


@pytest.mark.asyncio
async def test_add_event_success() -> None:
    test_event = create_test_event()

    with patch.object(EventService, "__init__", return_value=None):
        mock_repo = create_mock_repository()
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.add.return_value = test_event

        result = await service.add(test_event)

        service.repository.add.assert_called_once_with(test_event)
        assert result == test_event


@pytest.mark.asyncio
async def test_add_event_duplicate_id() -> None:
    mock_repo = create_mock_repository()
    test_event = create_test_event()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.add.side_effect = Exception("Duplicate ID")

        with pytest.raises(
            ValueError, match=re.escape("Мероприятие c таким ID уже существует.")
        ):
            await service.add(test_event)

        service.repository.add.assert_called_once_with(test_event)


@pytest.mark.asyncio
async def test_update_event_success() -> None:
    test_event = create_test_event()
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.update.return_value = None

        result = await service.update(test_event)

        service.repository.update.assert_called_once_with(test_event)
        assert result == test_event


@pytest.mark.asyncio
async def test_update_event_not_found() -> None:
    test_event = create_test_event(999)
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.update.side_effect = Exception("Not found")

        with pytest.raises(ValueError, match=re.escape("Мероприятие не найдено.")):
            await service.update(test_event)

        service.repository.update.assert_called_once_with(test_event)


@pytest.mark.asyncio
async def test_delete_event_success() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.delete.return_value = None

        await service.delete(1)

        service.repository.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_event_not_found() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.delete.side_effect = Exception("Not found")

        with pytest.raises(ValueError, match=re.escape("Мероприятие не найдено.")):
            await service.delete(999)

        service.repository.delete.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_search_events_success() -> None:
    test_events = [create_test_event(1), create_test_event(2)]
    search_params = {"status": "Активное"}
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.search.return_value = test_events

        result = await service.search(search_params)

        service.repository.search.assert_called_once_with(search_params)
        assert result == test_events
        assert len(result) == TWO


@pytest.mark.asyncio
async def test_search_events_not_found() -> None:
    search_params = {"status": "Несуществующий статус"}
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.search.side_effect = Exception("Not found")

        with pytest.raises(
            ValueError,
            match=re.escape("Мероприятие по переданным параметрам не найдено."),
        ):
            await service.search(search_params)

        service.repository.search.assert_called_once_with(search_params)


@pytest.mark.asyncio
async def test_complete_event_success() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.complete.return_value = None

        await service.complete(1)

        service.repository.complete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_complete_event_error() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.complete.side_effect = Exception("Error")

        with pytest.raises(
            ValueError, match=re.escape("Ошибка при завершении мероприятия")
        ):
            await service.complete(1)

        service.repository.complete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_users_by_event_success() -> None:
    test_users = [create_test_user(1), create_test_user(2)]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_users_by_event.return_value = test_users

        result = await service.get_users_by_event(1)

        service.repository.get_users_by_event.assert_called_once_with(1)
        assert result == test_users
        assert len(result) == TWO


@pytest.mark.asyncio
async def test_get_users_by_event_error() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_users_by_event.side_effect = Exception("Error")

        with pytest.raises(
            ValueError, match=re.escape("Ошибка при получении пользователей")
        ):
            await service.get_users_by_event(1)

        service.repository.get_users_by_event.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_activities_by_event_success() -> None:
    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_activities_by_event.return_value = [activity]

        result = await service.get_activities_by_event(1)

        service.repository.get_activities_by_event.assert_called_once_with(1)
        assert len(result) == 1
        assert result[0].activity_id == 1


@pytest.mark.asyncio
async def test_get_activities_by_event_error() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_activities_by_event.side_effect = Exception("Error")

        with pytest.raises(
            ValueError,
            match=re.escape("Ошибка при получении активностей для мероприятий"),
        ):
            await service.get_activities_by_event(1)

        service.repository.get_activities_by_event.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_lodgings_by_event_success() -> None:
    lodging = Lodging(
        lodging_id=1,
        price=20000,
        address="Улица Гоголя, 12",
        name="Four Seasons",
        type="Отель",
        rating=5,
        check_in=datetime(2023, 10, 10, 10, 0, 0),
        check_out=datetime(2023, 10, 10, 18, 0, 0),
    )
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_lodgings_by_event.return_value = [lodging]

        result = await service.get_lodgings_by_event(1)

        service.repository.get_lodgings_by_event.assert_called_once_with(1)
        assert len(result) == 1
        assert result[0].lodging_id == 1


@pytest.mark.asyncio
async def test_get_lodgings_by_event_error() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_lodgings_by_event.side_effect = Exception("Error")

        with pytest.raises(
            ValueError, match=re.escape("Ошибка при получении размещений")
        ):
            await service.get_lodgings_by_event(1)

        service.repository.get_lodgings_by_event.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_link_activities_success() -> None:
    activity_ids = [1, 2, 3]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.link_activities.return_value = None

        await service.link_activities(1, activity_ids)

        service.repository.link_activities.assert_called_once_with(
            1, activity_ids
        )


@pytest.mark.asyncio
async def test_link_activities_error() -> None:
    activity_ids = [1, 2, 3]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.link_activities.side_effect = Exception("Error")

        with pytest.raises(
            ValueError,
            match=re.escape("Ошибка при связывании активностей с мероприятием."),
        ):
            await service.link_activities(1, activity_ids)

        service.repository.link_activities.assert_called_once_with(
            1, activity_ids
        )


@pytest.mark.asyncio
async def test_link_users_success() -> None:
    user_ids = [1, 2, 3]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.link_users.return_value = None

        await service.link_users(1, user_ids)

        service.repository.link_users.assert_called_once_with(1, user_ids)


@pytest.mark.asyncio
async def test_link_users_error() -> None:
    user_ids = [1, 2, 3]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.link_users.side_effect = Exception("Error")

        with pytest.raises(
            ValueError,
            match=re.escape("Ошибка при связывании пользователей с мероприятием."),
        ):
            await service.link_users(1, user_ids)

        service.repository.link_users.assert_called_once_with(1, user_ids)


@pytest.mark.asyncio
async def test_link_lodgings_success() -> None:
    lodging_ids = [1, 2, 3]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.link_lodgings.return_value = None

        await service.link_lodgings(1, lodging_ids)

        service.repository.link_lodgings.assert_called_once_with(
            1, lodging_ids
        )


@pytest.mark.asyncio
async def test_link_lodgings_error() -> None:
    lodging_ids = [1, 2, 3]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.link_lodgings.side_effect = Exception("Error")

        with pytest.raises(
            ValueError,
            match=re.escape("Ошибка при связывании размещений с мероприятием."),
        ):
            await service.link_lodgings(1, lodging_ids)

        service.repository.link_lodgings.assert_called_once_with(
            1, lodging_ids
        )


@pytest.mark.asyncio
async def test_get_events_for_user_success() -> None:
    test_events = [create_test_event(1), create_test_event(2)]
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_events_for_user.return_value = test_events

        result = await service.get_events_for_user(1, "active")

        service.repository.get_events_for_user.assert_called_once_with(1, "active")
        assert result == test_events
        assert len(result) == TWO


@pytest.mark.asyncio
async def test_get_events_for_user_error() -> None:
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_events_for_user.side_effect = Exception("Error")

        with pytest.raises(
            ValueError, match=re.escape("Ошибка при получении активных мероприятий")
        ):
            await service.get_events_for_user(1, "active")

        service.repository.get_events_for_user.assert_called_once_with(1, "active")


@pytest.mark.asyncio
async def test_get_event_by_session_id_success() -> None:
    test_event = create_test_event()
    mock_repo = create_mock_repository()
    with patch.object(EventService, "__init__", return_value=None):
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_event_by_session_id.return_value = test_event

        result = await service.get_event_by_session_id(123)

        service.repository.get_event_by_session_id.assert_called_once_with(123)
        assert result == test_event


@pytest.mark.asyncio
async def test_get_event_by_session_id_not_found() -> None:
    with patch.object(EventService, "__init__", return_value=None):
        mock_repo = create_mock_repository()
        service = EventService(mock_repo)
        service.repository = AsyncMock()
        service.repository.get_event_by_session_id.side_effect = Exception("Not found")

        with pytest.raises(ValueError):
            await service.get_event_by_session_id(999)

        service.repository.get_event_by_session_id.assert_called_once_with(999)



