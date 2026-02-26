from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_get_non_existing_venue_returns_none(venue_service: VenueService) -> None:
    venue = await venue_service.get_by_id(999)
    assert venue is None
