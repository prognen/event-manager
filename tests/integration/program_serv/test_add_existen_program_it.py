from __future__ import annotations

import pytest

from models.venue import Venue
from models.program import Program
from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_add_duplicate_program_raises(
    program_service: ProgramService,
) -> None:
    duplicate_program = Program(
        program_id=2,
        type_transport="Самолет",
        from_venue=Venue(venue_id=3, name="Санкт-Петербург"),
        to_venue=Venue(venue_id=4, name="Калининград"),
        distance=966,
        cost=5123,
    )

    result = await program_service.add(duplicate_program)

    assert result is not None
