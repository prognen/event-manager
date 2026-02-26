from __future__ import annotations

from datetime import datetime

import pytest

from models.lodging import Lodging
from models.venue import Venue
from services.lodging_service import LodgingService


THIRD = 3


@pytest.mark.asyncio
async def test_add_accommodation_success(
    lodging_service: LodgingService,
) -> None:
    new_accommodation = Lodging(
        lodging_id=3,
        price=15000,
        address="Улица Ленина, 10",
        name="Новый Отель",
        type="Отель",
        rating=5,
        check_in=datetime(2025, 3, 29, 12, 30, 0),
        check_out=datetime(2025, 4, 5, 18, 0, 0),
        venue=Venue(venue_id=1, name="Москва"),
    )

    await lodging_service.add(new_accommodation)
    result = await lodging_service.get_by_id(3)
    assert result is not None
    assert result.name == "Новый Отель"
    assert result.lodging_id == THIRD



