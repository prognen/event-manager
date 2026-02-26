from __future__ import annotations

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_add_venue_success(venue_service: VenueService) -> None:
    new_venue = Venue(venue_id=6, name="Рязань")

    result = await venue_service.add(new_venue)

    assert result.name == "Рязань"

    venue_in_db = await venue_service.get_by_id(result.venue_id)
    assert venue_in_db is not None
    assert venue_in_db.name == "Рязань"
