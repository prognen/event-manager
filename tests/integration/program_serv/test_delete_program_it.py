from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_delete_program_success(
    program_service: ProgramService,
) -> None:
    await program_service.delete(3)

    deleted = await program_service.get_by_id(3)
    assert deleted is None



