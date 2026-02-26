from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_get_program_by_id_not_found(
    program_service: ProgramService,
) -> None:
    result = await program_service.get_by_id(999)

    assert result is None



