from __future__ import annotations

from datetime import datetime

import pytest

from models.lodging import Lodging
from models.venue import Venue
from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_update_existing_accommodation(
    lodging_service: LodgingService,
) -> None:
    updated = Lodging(
        lodging_id=1,
        price=20000,
        address="ул. Пушкина, 5",
        name="Обновленный отель",
        type="Отель",
        rating=5,
        check_in=datetime(2025, 3, 29, 12, 30, 0),
        check_out=datetime(2025, 4, 5, 18, 0, 0),
        venue=Venue(venue_id=2, name="Воронеж"),
    )

    result = await lodging_service.update(updated)

    assert result is not None
    assert result.name == "Обновленный отель"



