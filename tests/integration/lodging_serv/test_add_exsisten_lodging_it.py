from __future__ import annotations

import re

from datetime import datetime

import pytest

from models.lodging import Lodging
from models.venue import Venue
from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_add_duplicate_name_accommodation_raises(
    lodging_service: LodgingService,
) -> None:
    existing_accommodation = Lodging(
        lodging_id=2,
        price=33450,
        address="ул. Дмитриевского, 7",
        name="ABC",
        type="Квартира",
        rating=3,
        check_in=datetime(2025, 4, 2, 14, 0, 0),
        check_out=datetime(2025, 4, 6, 18, 0, 0),
        Venue=Venue(venue_id=1, name="Москва"),
    )
    with pytest.raises(
        ValueError, match=re.escape("Размещение c таким ID уже существует.")
    ):
        await lodging_service.add(existing_accommodation)



