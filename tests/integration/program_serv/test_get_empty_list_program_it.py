from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_get_empty_list(program_service: ProgramService) -> None:
    for i in range(1, 13):
        await program_service.delete(i)
    programs = await program_service.get_list()

    assert len(programs) == 0



