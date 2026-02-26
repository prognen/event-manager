from __future__ import annotations

import pytest

from services.venue_service import VenueService


TMP = 5


@pytest.mark.asyncio
async def test_get_all_cities_success(venue_service: VenueService) -> None:
    cities = await venue_service.get_all_venues()

    assert cities is not None
    assert len(cities) == TMP


