from __future__ import annotations

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_update_existing_venue(venue_service: VenueService) -> None:
    updated_venue = Venue(venue_id=1, name="Адлер")
    result = await venue_service.update(updated_venue)

    assert result.name == "Адлер"

    venue_in_db = await venue_service.get_by_id(1)
    assert venue_in_db is not None
    assert venue_in_db.name == "Адлер"
