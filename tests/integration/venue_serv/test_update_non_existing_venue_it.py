from __future__ import annotations

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_update_non_existing_city_raises(venue_service: VenueService) -> None:
    city_before = await venue_service.get_by_id(999)
    assert city_before is None

    non_existing_city = Venue(venue_id=999, name="Новый Город")

    await venue_service.update(non_existing_city)

    city_after = await venue_service.get_by_id(999)
    assert city_after is None



