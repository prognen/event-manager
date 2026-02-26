from __future__ import annotations

import pytest

from services.program_service import ProgramService


TMP = 12


@pytest.mark.asyncio
async def test_get_list_directory_routes(
    program_service: ProgramService,
) -> None:
    routes = await program_service.get_list()

    assert len(routes) == TMP
    names = [r.type_transport for r in routes]
    assert "Паром" in names
    assert "Самолет" in names
    assert "Автобус" in names



