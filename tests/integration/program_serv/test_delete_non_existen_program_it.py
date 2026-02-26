from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_delete_non_existing_program_raises(
    program_service: ProgramService,
) -> None:
    await program_service.delete(999)

    program = await program_service.get_by_id(999)
    assert program is None



