from __future__ import annotations

import pytest

from models.venue import Venue
from models.program import DirectoryRoute
from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_update_non_existing_directory_route_raises(
    program_service: ProgramService,
) -> None:
    fake_route = DirectoryRoute(
        program_id=999,
        type_transport="Паром",
        from_venue=Venue(venue_id=3, name="Санкт-Петербург"),
        destination_city=Venue(venue_id=5, name="Екатеринбург"),
        distance=100,
        cost=50,
    )

    await program_service.update(fake_route)
    result = await program_service.get_by_id(999)
    assert result is None



