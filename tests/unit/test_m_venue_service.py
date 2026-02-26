from __future__ import annotations

import re

from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from models.venue import Venue
from repository.venue_repository import VenueRepository
from services.venue_service import VenueService


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_service_should_successfull_delete_existed_city(
    mock_venue_repo: Mock,
) -> None:
    # Arrange
    venue_service = VenueService(mock_venue_repo)

    # Act
    await venue_service.delete(123)

    # Assert
    mock_venue_repo.delete.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_delete_not_existed_city() -> None:
    repository = Mock(spec=VenueRepository)
    repository.delete = AsyncMock(side_effect=ValueError("Not found"))

    venue_service = VenueService(repository)

    with pytest.raises(ValueError):
        await venue_service.delete(123)


@pytest.mark.asyncio
async def test_should_succesfull_get_cities() -> None:
    cities = [Venue(venue_id=1, name="Москва"), Venue(venue_id=2, name="Казань")]
    repository = Mock(spec=VenueRepository)
    repository.get_list = AsyncMock(return_value=cities)

    venue_service = VenueService(repository)
    result = await venue_service.get_all_venues()

    assert result == cities
    repository.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_should_call_get_list_on_repository() -> None:
    repository = Mock(spec=VenueRepository)
    repository.get_list = AsyncMock()

    venue_service = VenueService(repository)

    await venue_service.get_all_venues()

    repository.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_success() -> None:
    venue = Venue(venue_id=3, name="Воронеж")
    repo = Mock(spec=VenueRepository)
    repo.add = AsyncMock(return_value=venue)

    service = VenueService(repo)
    result = await service.add(venue)

    assert result == venue
    repo.add.assert_awaited_once_with(venue)


@pytest.mark.asyncio
async def test_add_failure_duplicate() -> None:
    venue = Venue(venue_id=3, name="Воронеж")
    repo = Mock(spec=VenueRepository)
    repo.add = AsyncMock(side_effect=Exception("Duplicate"))

    service = VenueService(repo)

    with pytest.raises(ValueError, match=re.escape("Площадка c таким ID уже существует.")):
        await service.add(venue)


@pytest.mark.asyncio
async def test_get_all_cities_failure() -> None:
    repo = Mock(spec=VenueRepository)
    repo.get_list = AsyncMock(side_effect=Exception("db error"))

    service = VenueService(repo)

    with pytest.raises(Exception):
        await service.get_all_venues()


@pytest.mark.asyncio
async def test_should_succesfull_get_existed_city_by_id() -> None:
    venue = Venue(venue_id=1, name="Москва")
    repository = Mock(spec=VenueRepository)
    repository.get_by_id = AsyncMock(return_value=venue)

    venue_service = VenueService(repository)
    result = await venue_service.get_by_id(1)

    assert result == venue
    repository.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_service_should_call_get_by_id_on_repository() -> None:
    repository = Mock(spec=VenueRepository)
    repository.get_by_id = AsyncMock()

    venue_service = VenueService(repository)

    await venue_service.get_by_id(1)

    repository.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_get_not_existed_city() -> None:
    repository = Mock(spec=VenueRepository)
    repository.get_by_id = AsyncMock(side_effect=ValueError("Not found"))

    venue_service = VenueService(repository)

    with pytest.raises(ValueError):
        await venue_service.get_by_id(123)


@pytest.mark.asyncio
async def test_should_succesfull_update_existed_city_by_id() -> None:
    venue = Venue(venue_id=1, name="Москва")
    repository = Mock(spec=VenueRepository)
    repository.update = AsyncMock(return_value=venue)

    venue_service = VenueService(repository)
    result = await venue_service.update(venue)

    assert result == venue
    repository.update.assert_awaited_once_with(venue)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_update_not_existed_city() -> None:
    venue = Venue(venue_id=1, name="Москва")
    repository = Mock(spec=VenueRepository)
    repository.update = AsyncMock(side_effect=ValueError("Not found"))

    venue_service = VenueService(repository)

    with pytest.raises(ValueError):
        await venue_service.update(venue)
