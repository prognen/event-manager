from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_update_program_success(
    program_service: ProgramService,
) -> None:
    program = await program_service.get_by_id(2)
    assert program is not None

    program.type_transport = "Поезд"
    await program_service.update(program)

    updated = await program_service.get_by_id(2)
    assert updated is not None
    assert updated.type_transport == "Поезд"



