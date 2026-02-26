from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_delete_non_existing_program_raises(
    program_service: ProgramService,
) -> None:
    with pytest.raises(ValueError):
        await program_service.delete(999)


