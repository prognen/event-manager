from __future__ import annotations

import re

from datetime import datetime
from unittest.mock import Mock

import pytest

from models.activity import Activity
from services.activity_service import ActivityService


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_service_should_successfull_delete_existed_entertainment(
    mock_activity_repo: Mock,
) -> None:
    service = ActivityService(mock_activity_repo)

    await service.delete(123)

    mock_activity_repo.delete.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_delete_not_existed_entertainment(
    mock_activity_repo: Mock,
) -> None:
    mock_activity_repo.delete.side_effect = Exception("Not found")
    service = ActivityService(mock_activity_repo)

    with pytest.raises(ValueError, match=re.escape("Активность не найдена.")):
        await service.delete(123)

    mock_activity_repo.delete.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_should_succesfull_get_existed_entertainment_by_id(
    mock_activity_repo: Mock,
) -> None:
    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )
    mock_activity_repo.get_by_id.return_value = activity
    service = ActivityService(mock_activity_repo)

    result = await service.get_by_id(1)

    assert result == activity
    mock_activity_repo.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_by_id_failure(mock_activity_repo: Mock) -> None:
    mock_activity_repo.get_by_id.side_effect = ValueError("Not found")
    service = ActivityService(mock_activity_repo)

    with pytest.raises(ValueError):
        await service.get_by_id(123)


@pytest.mark.asyncio
async def test_get_list_success(mock_activity_repo: Mock) -> None:
    entertainments = [
        Activity(
            activity_id=1,
            duration="4 часа",
            address="Главная площадь",
            activity_type="Выставка",
            activity_time=datetime(2023, 10, 10, 10, 0, 0),
        )
    ]
    mock_activity_repo.get_list.return_value = entertainments
    service = ActivityService(mock_activity_repo)

    result = await service.get_list()

    assert result == entertainments
    mock_activity_repo.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_list_failure(mock_activity_repo: Mock) -> None:
    mock_activity_repo.get_list.side_effect = ValueError("Database error")
    service = ActivityService(mock_activity_repo)

    with pytest.raises(ValueError):
        await service.get_list()


@pytest.mark.asyncio
async def test_add_success(mock_activity_repo: Mock) -> None:
    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )
    mock_activity_repo.add.return_value = activity
    service = ActivityService(mock_activity_repo)

    result = await service.add(activity)

    assert result == activity
    mock_activity_repo.add.assert_awaited_once_with(activity)


@pytest.mark.asyncio
async def test_add_failure(mock_activity_repo: Mock) -> None:
    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )
    mock_activity_repo.add.side_effect = ValueError("Duplicate")
    service = ActivityService(mock_activity_repo)

    with pytest.raises(ValueError):
        await service.add(activity)


@pytest.mark.asyncio
async def test_update_success(mock_activity_repo: Mock) -> None:
    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )
    mock_activity_repo.update.return_value = activity
    service = ActivityService(mock_activity_repo)

    result = await service.update(activity)

    assert result == activity
    mock_activity_repo.update.assert_awaited_once_with(activity)


@pytest.mark.asyncio
async def test_update_failure(mock_activity_repo: Mock) -> None:
    activity = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Выставка",
        activity_time=datetime(2023, 10, 10, 10, 0, 0),
    )
    mock_activity_repo.update.side_effect = ValueError("Not found")
    service = ActivityService(mock_activity_repo)

    with pytest.raises(ValueError):
        await service.update(activity)



