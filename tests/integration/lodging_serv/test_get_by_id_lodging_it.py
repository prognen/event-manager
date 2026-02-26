from __future__ import annotations

import pytest

from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_get_accommodation_by_id_success(
    lodging_service: LodgingService,
) -> None:
    lodging = await lodging_service.get_by_id(1)

    assert lodging is not None
    assert lodging.name == "ABC"
    assert lodging.lodging_id == 1


