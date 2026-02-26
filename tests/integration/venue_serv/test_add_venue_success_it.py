from __future__ import annotations

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_add_city_success(venue_service: VenueService) -> None:
    new_city = Venue(venue_id=6, name="Рязань")

    result = await venue_service.add(new_city)

    assert result.name == "Рязань"

    city_in_db = await venue_service.get_by_id(6)
    assert city_in_db is not None
    assert city_in_db.name == "Рязань"



