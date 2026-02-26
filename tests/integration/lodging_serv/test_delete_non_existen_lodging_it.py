from __future__ import annotations

import pytest

from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_delete_non_existing_accommodation_raises(
    lodging_service: LodgingService,
) -> None:
    with pytest.raises(ValueError):
        await lodging_service.delete(999)


