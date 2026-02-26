from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_get_all_cities_empty_list(venue_service: VenueService) -> None:
    for i in range(1, 6):
        await venue_service.delete(i)
    cities = await venue_service.get_all_cities()

    assert len(cities) == 0



