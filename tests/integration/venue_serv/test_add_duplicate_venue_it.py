from __future__ import annotations

import re

import pytest

from models.venue import Venue
from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_add_duplicate_venue_raises(venue_service: VenueService) -> None:
    venue_obj = Venue(venue_id=1, name="Москва")
    with pytest.raises(ValueError, match=re.escape("Площадка c таким ID уже существует.")):
        await venue_service.add(venue_obj)


