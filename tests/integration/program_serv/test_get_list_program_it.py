from __future__ import annotations

import pytest

from services.program_service import ProgramService


EXPECTED_COUNT = 12


@pytest.mark.asyncio
async def test_get_list_programs(
    program_service: ProgramService,
) -> None:
    programs = await program_service.get_list()

    assert len(programs) == EXPECTED_COUNT
    transport_types = [p.type_transport for p in programs]
    assert "Паром" in transport_types
    assert "Самолет" in transport_types
    assert "Автобус" in transport_types
