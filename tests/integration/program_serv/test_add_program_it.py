from __future__ import annotations

import pytest

from models.venue import Venue
from models.program import Program
from services.program_service import ProgramService


FOUR = 13


@pytest.mark.asyncio
async def test_add_program_success(
    program_service: ProgramService,
) -> None:
    new_program = Program(
        program_id=13,
        type_transport="Поезд",
        from_venue=Venue(venue_id=1, name="Москва"),
        to_venue=Venue(venue_id=5, name="Екатеринбург"),
        distance=600,
        cost=2000,
    )

    result = await program_service.add(new_program)

    assert result.program_id == FOUR
    assert result.type_transport == "Поезд"
