from __future__ import annotations

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_update_non_existing_venue_raises(venue_service: VenueService) -> None:
    venue_before = await venue_service.get_by_id(999)
    assert venue_before is None

    non_existing_venue = Venue(venue_id=999, name="Новая Площадка")

    with pytest.raises(ValueError):
        await venue_service.update(non_existing_venue)
