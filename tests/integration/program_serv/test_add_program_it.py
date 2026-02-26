from __future__ import annotations

import pytest

from models.venue import Venue
from models.program import DirectoryRoute
from services.program_service import ProgramService


FOUR = 13


@pytest.mark.asyncio
async def test_add_directory_route_success(
    program_service: ProgramService,
) -> None:
    new_route = DirectoryRoute(
        program_id=13,
        type_transport="Поезд",
        from_venue=Venue(venue_id=1, name="Москва"),
        destination_city=Venue(venue_id=5, name="Екатеринбург"),
        distance=600,
        cost=2000,
    )

    result = await program_service.add(new_route)

    assert result.program_id == FOUR
    assert result.type_transport == "Поезд"



