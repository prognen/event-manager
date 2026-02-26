from __future__ import annotations

import pytest

from services.venue_service import VenueService


@pytest.mark.asyncio
async def test_delete_non_existing_venue_raises(venue_service: VenueService) -> None:
    with pytest.raises(ValueError):
        await venue_service.delete(999)
