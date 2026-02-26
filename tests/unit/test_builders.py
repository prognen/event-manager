"""
Тесты, демонстрирующие использование паттернов Data Builder и Object Mother
для генерации тестовых объектов (требование 7 лабораторной работы).

Data Builder — цепочка методов (fluent API) для точечного переопределения полей.
Object Mother — фабричные методы с готовыми «семантически осмысленными» объектами.
"""
from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from builders import ActivityMother
from builders import EventMother
from builders import LodgingMother
from builders import UserMother
from builders import VenueBuilder
from builders import VenueMother
from builders import ActivityBuilder
from builders import LodgingBuilder
from builders import UserBuilder
from repository.venue_repository import VenueRepository
from repository.activity_repository import ActivityRepository
from repository.lodging_repository import LodgingRepository
from repository.event_repository import EventRepository
from services.venue_service import VenueService
from services.activity_service import ActivityService
from services.lodging_service import LodgingService
from services.event_service import EventService


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Тесты паттерна Object Mother
# ---------------------------------------------------------------------------


class TestVenueMother:
    """Тесты, использующие VenueMother для генерации объектов."""

    @pytest.mark.asyncio
    async def test_get_venue_by_id_using_mother(self) -> None:
        """Позитивный тест: получение площадки через ObjectMother."""
        venue = VenueMother.moscow()
        repo = Mock(spec=VenueRepository)
        repo.get_by_id = AsyncMock(return_value=venue)
        service = VenueService(repo)

        result = await service.get_by_id(venue.venue_id)

        assert result == venue
        assert result.name == "Конгресс-центр Москва"

    @pytest.mark.asyncio
    async def test_add_venue_using_mother_duplicate(self) -> None:
        """Негативный тест: добавление дубликата площадки через ObjectMother."""
        venue = VenueMother.saint_petersburg()
        repo = Mock(spec=VenueRepository)
        repo.add = AsyncMock(side_effect=Exception("Duplicate"))
        service = VenueService(repo)

        with pytest.raises(ValueError, match="Площадка c таким ID уже существует."):
            await service.add(venue)


class TestActivityMother:
    """Тесты, использующие ActivityMother для генерации объектов."""

    @pytest.mark.asyncio
    async def test_get_activity_using_mother(self) -> None:
        """Позитивный тест: получение активности через ObjectMother."""
        activity = ActivityMother.exhibition()
        repo = Mock(spec=ActivityRepository)
        repo.get_by_id = AsyncMock(return_value=activity)
        service = ActivityService(repo)

        result = await service.get_by_id(activity.activity_id)

        assert result == activity
        assert result.activity_type == "Выставка"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_activity_using_mother(self) -> None:
        """Негативный тест: удаление несуществующей активности."""
        repo = Mock(spec=ActivityRepository)
        repo.delete = AsyncMock(side_effect=Exception("Not found"))
        service = ActivityService(repo)

        with pytest.raises(ValueError, match="Активность не найдена."):
            await service.delete(9999)


class TestLodgingMother:
    """Тесты, использующие LodgingMother для генерации объектов."""

    @pytest.mark.asyncio
    async def test_add_hotel_using_mother(self) -> None:
        """Позитивный тест: добавление размещения через ObjectMother."""
        lodging = LodgingMother.hotel()
        repo = Mock(spec=LodgingRepository)
        repo.add = AsyncMock(return_value=lodging)
        service = LodgingService(repo)

        result = await service.add(lodging)

        assert result == lodging
        assert result.rating == 5

    @pytest.mark.asyncio
    async def test_get_hostel_by_id_not_found(self) -> None:
        """Негативный тест: поиск несуществующего размещения через ObjectMother."""
        repo = Mock(spec=LodgingRepository)
        repo.get_by_id = AsyncMock(side_effect=ValueError("Not found"))
        service = LodgingService(repo)

        with pytest.raises(ValueError):
            await service.get_by_id(9999)


# ---------------------------------------------------------------------------
# Тесты паттерна Data Builder (fluent API)
# ---------------------------------------------------------------------------


class TestVenueBuilder:
    """Тесты, использующие VenueBuilder (fluent API)."""

    @pytest.mark.asyncio
    async def test_get_custom_venue_via_builder(self) -> None:
        """Позитивный тест: получение площадки, созданной через Builder."""
        venue = VenueBuilder().with_id(42).with_name("Сколково Экспо").build()
        repo = Mock(spec=VenueRepository)
        repo.get_by_id = AsyncMock(return_value=venue)
        service = VenueService(repo)

        result = await service.get_by_id(42)

        assert result.venue_id == 42
        assert result.name == "Сколково Экспо"

    @pytest.mark.asyncio
    async def test_update_custom_venue_not_found(self) -> None:
        """Негативный тест: обновление несуществующей площадки через Builder."""
        venue = VenueBuilder().with_id(999).with_name("Несуществующая").build()
        repo = Mock(spec=VenueRepository)
        repo.update = AsyncMock(side_effect=Exception("Not found"))
        service = VenueService(repo)

        with pytest.raises(ValueError, match="Площадка не найдена."):
            await service.update(venue)


class TestActivityBuilder:
    """Тесты, использующие ActivityBuilder (fluent API)."""

    @pytest.mark.asyncio
    async def test_add_custom_activity_via_builder(self) -> None:
        """Позитивный тест: добавление активности, созданной через Builder."""
        from datetime import datetime
        activity = (
            ActivityBuilder()
            .with_id(10)
            .with_type("Церемония")
            .with_duration("3 часа")
            .with_address("Главная сцена")
            .with_time(datetime(2025, 9, 1, 18, 0, 0))
            .build()
        )
        repo = Mock(spec=ActivityRepository)
        repo.add = AsyncMock(return_value=activity)
        service = ActivityService(repo)

        result = await service.add(activity)

        assert result.activity_id == 10
        assert result.activity_type == "Церемония"

    @pytest.mark.asyncio
    async def test_update_custom_activity_failure(self) -> None:
        """Негативный тест: обновление несуществующей активности через Builder."""
        from datetime import datetime
        activity = (
            ActivityBuilder()
            .with_id(999)
            .with_type("Экскурсия")
            .with_duration("1 час")
            .with_address("Старый город")
            .with_time(datetime(2025, 9, 1, 10, 0, 0))
            .build()
        )
        repo = Mock(spec=ActivityRepository)
        repo.update = AsyncMock(side_effect=Exception("Not found"))
        service = ActivityService(repo)

        with pytest.raises(ValueError):
            await service.update(activity)


class TestUserBuilder:
    """Тесты, использующие UserBuilder и UserMother."""

    def test_default_user_via_mother(self) -> None:
        """Позитивный тест: создание пользователя по умолчанию через ObjectMother."""
        user = UserMother.default()

        assert user.user_id == 1
        assert user.login == "ivan_user"

    def test_custom_user_via_builder(self) -> None:
        """Позитивный тест: создание пользователя с кастомными полями через Builder."""
        user = (
            UserBuilder()
            .with_id(99)
            .with_fio("Сидоров Сидор Сидорович")
            .with_email("sidorov@test.ru")
            .with_login("sidorov99")
            .build()
        )

        assert user.user_id == 99
        assert user.fio == "Сидоров Сидор Сидорович"
        assert user.login == "sidorov99"

    def test_admin_user_via_mother(self) -> None:
        """Позитивный тест: создание администратора через ObjectMother."""
        admin = UserMother.admin()

        assert admin.login == "admin"
        assert admin.email == "admin@eventmanager.ru"


class TestEventBuilder:
    """Тесты, использующие EventMother для сложных агрегатов."""

    def test_active_event_via_mother(self) -> None:
        """Позитивный тест: создание активного мероприятия через ObjectMother."""
        event = EventMother.active()

        assert event.status == "Активное"
        assert len(event.users) > 0
        assert len(event.activities) > 0
        assert len(event.lodgings) > 0

    def test_completed_event_via_mother(self) -> None:
        """Позитивный тест: создание завершённого мероприятия через ObjectMother."""
        event = EventMother.completed()

        assert event.status == "Завершено"
        assert event.event_id == 2

    @pytest.mark.asyncio
    async def test_get_event_by_id_using_mother(self) -> None:
        """Позитивный тест: получение мероприятия через ObjectMother."""
        from unittest.mock import patch
        from typing import cast
        from abstract_repository.ievent_repository import IEventRepository

        event = EventMother.active()
        mock_repo = AsyncMock(spec=IEventRepository)
        mock_repo.get_by_id = AsyncMock(return_value=event)

        with patch.object(EventService, "__init__", return_value=None):
            service = EventService(cast(IEventRepository, mock_repo))
            service.repository = mock_repo

            result = await service.get_by_id(event.event_id)

            assert result == event

    @pytest.mark.asyncio
    async def test_add_duplicate_event_using_mother(self) -> None:
        """Негативный тест: добавление дублирующего мероприятия через ObjectMother."""
        from unittest.mock import patch
        from typing import cast
        from abstract_repository.ievent_repository import IEventRepository

        event = EventMother.cancelled()
        mock_repo = AsyncMock(spec=IEventRepository)
        mock_repo.add = AsyncMock(side_effect=Exception("Duplicate ID"))

        with patch.object(EventService, "__init__", return_value=None):
            service = EventService(cast(IEventRepository, mock_repo))
            service.repository = mock_repo

            with pytest.raises(ValueError, match="Мероприятие c таким ID уже существует."):
                await service.add(event)


class TestLodgingBuilder:
    """Тесты, использующие LodgingBuilder (fluent API)."""

    @pytest.mark.asyncio
    async def test_update_cheap_lodging_via_builder(self) -> None:
        """Позитивный тест: обновление бюджетного размещения через Builder."""
        from datetime import datetime
        lodging = (
            LodgingBuilder()
            .with_id(5)
            .with_name("Хостел Молодёжный")
            .with_type("Хостел")
            .with_price(900)
            .with_rating(3)
            .with_dates(datetime(2025, 7, 1, 14, 0), datetime(2025, 7, 5, 12, 0))
            .build()
        )
        repo = Mock(spec=LodgingRepository)
        repo.update = AsyncMock(return_value=lodging)
        service = LodgingService(repo)

        result = await service.update(lodging)

        assert result.price == 900
        assert result.type == "Хостел"

    @pytest.mark.asyncio
    async def test_delete_lodging_via_builder_not_found(self) -> None:
        """Негативный тест: удаление несуществующего размещения через Builder."""
        repo = Mock(spec=LodgingRepository)
        repo.delete = AsyncMock(side_effect=Exception("Not found"))
        service = LodgingService(repo)

        with pytest.raises(ValueError, match="Размещение не найдено."):
            await service.delete(9999)
