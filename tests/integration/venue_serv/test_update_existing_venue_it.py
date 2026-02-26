from __future__ import annotations

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_update_existing_city(venue_service: VenueService) -> None:
    updated_city = Venue(venue_id=1, name="Адлер")
    result = await venue_service.update(updated_city)

    assert result.name == "Адлер"

    city_in_db = await venue_service.get_by_id(1)
    assert city_in_db is not None
    assert city_in_db.name == "Адлер"



