from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest

from models.lodging import Lodging
from services.lodging_service import LodgingService


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_delete_success(mock_lodging_repo: Mock) -> None:
    service = LodgingService(mock_lodging_repo)

    await service.delete(123)

    mock_lodging_repo.delete.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_delete_failure(mock_lodging_repo: Mock) -> None:
    mock_lodging_repo.delete.side_effect = ValueError("Not found")
    service = LodgingService(mock_lodging_repo)

    with pytest.raises(ValueError):
        await service.delete(123)


@pytest.mark.asyncio
async def test_should_succesfull_get_existed_accommodation_by_id(
    mock_lodging_repo: Mock,
) -> None:
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

    mock_lodging_repo.get_by_id.return_value = lodging
    service = LodgingService(mock_lodging_repo)

    result = await service.get_by_id(1)

    assert result == lodging
    mock_lodging_repo.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_by_id_failure(mock_lodging_repo: Mock) -> None:
    mock_lodging_repo.get_by_id.side_effect = ValueError("Not found")
    service = LodgingService(mock_lodging_repo)

    with pytest.raises(ValueError):
        await service.get_by_id(123)


@pytest.mark.asyncio
async def test_get_list_success(mock_lodging_repo: Mock) -> None:
    accommodations = [
        Lodging(
            lodging_id=1,
            price=20000,
            address="Улица Гоголя, 12",
            name="Four Seasons",
            type="Отель",
            rating=5,
            check_in=datetime(2023, 10, 10, 10, 0, 0),
            check_out=datetime(2023, 10, 10, 18, 0, 0),
        )
    ]
    mock_lodging_repo.get_list.return_value = accommodations
    service = LodgingService(mock_lodging_repo)

    result = await service.get_list()

    assert result == accommodations
    mock_lodging_repo.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_list_failure(mock_lodging_repo: Mock) -> None:
    mock_lodging_repo.get_list.side_effect = ValueError("Database error")
    service = LodgingService(mock_lodging_repo)

    with pytest.raises(ValueError):
        await service.get_list()


@pytest.mark.asyncio
async def test_add_success(mock_lodging_repo: Mock) -> None:
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
    mock_lodging_repo.add.return_value = lodging
    service = LodgingService(mock_lodging_repo)

    result = await service.add(lodging)

    assert result == lodging
    mock_lodging_repo.add.assert_awaited_once_with(lodging)


@pytest.mark.asyncio
async def test_add_failure(mock_lodging_repo: Mock) -> None:
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
    mock_lodging_repo.add.side_effect = ValueError("Duplicate")
    service = LodgingService(mock_lodging_repo)

    with pytest.raises(ValueError):
        await service.add(lodging)


@pytest.mark.asyncio
async def test_update_success(mock_lodging_repo: Mock) -> None:
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
    service = LodgingService(mock_lodging_repo)
    mock_lodging_repo.update.return_value = lodging

    result = await service.update(lodging)

    assert result == lodging
    mock_lodging_repo.update.assert_awaited_once_with(lodging)


@pytest.mark.asyncio
async def test_update_failure(mock_lodging_repo: Mock) -> None:
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
    mock_lodging_repo.update.side_effect = ValueError("Not found")
    service = LodgingService(mock_lodging_repo)

    with pytest.raises(ValueError):
        await service.update(lodging)



