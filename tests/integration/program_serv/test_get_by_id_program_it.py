from __future__ import annotations

import pytest

from services.program_service import ProgramService


@pytest.mark.asyncio
async def test_get_directory_route_by_id_success(
    program_service: ProgramService,
) -> None:
    d_route = await program_service.get_by_id(1)

    assert d_route is not None
    assert d_route.program_id == 1
    assert d_route.type_transport in {"Паром", "Самолет", "Автобус"}



