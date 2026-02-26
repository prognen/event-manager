from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.venue import Venue


class IVenueRepository(ABC):
    @abstractmethod
    async def get_list(self) -> list[Venue]:
        pass

    @abstractmethod
    async def get_by_id(self, venue_id: int) -> Venue | None:
        pass

    @abstractmethod
    async def add(self, venue: Venue) -> Venue:
        pass

    @abstractmethod
    async def update(self, update_venue: Venue) -> None:
        pass

    @abstractmethod
    async def delete(self, venue_id: int) -> None:
        pass
