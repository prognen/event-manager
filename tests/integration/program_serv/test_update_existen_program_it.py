from __future__ import annotations

import pytest

from models.venue import Venue
from models.program import Program
from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_update_non_existing_program_raises(
    program_service: ProgramService,
) -> None:
    fake_program = Program(
        program_id=999,
        type_transport="Паром",
        from_venue=Venue(venue_id=3, name="Санкт-Петербург"),
        to_venue=Venue(venue_id=5, name="Екатеринбург"),
        distance=100,
        cost=50,
    )

    with pytest.raises(ValueError):
        await program_service.update(fake_program)


