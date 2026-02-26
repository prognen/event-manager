from __future__ import annotations

from datetime import datetime

import pytest

from models.lodging import Lodging
from models.venue import Venue
from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_update_accommodation_raises(
    lodging_service: LodgingService,
) -> None:
    non_existing = Lodging(
        lodging_id=999,
        price=1000,
        address="Улица Ленина, 10",
        name="Несуществующее размещение",
        type="Отель",
        rating=5,
        check_in=datetime(2025, 3, 29, 12, 30, 0),
        check_out=datetime(2025, 4, 5, 18, 0, 0),
        Venue=Venue(venue_id=1, name="Москва"),
    )

    await lodging_service.update(non_existing)

    result = await lodging_service.get_by_id(999)
    assert result is None



