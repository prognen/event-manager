from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_get_program_by_id_success(
    program_service: ProgramService,
) -> None:
    program = await program_service.get_by_id(1)

    assert program is not None
    assert program.program_id == 1
    assert program.type_transport in {"Паром", "Самолет", "Автобус"}



