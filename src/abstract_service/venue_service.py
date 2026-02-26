from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from models.venue import Venue


class IVenueService(ABC):
    @abstractmethod
    async def get_by_id(self, venue_id: int) -> Venue | None:
        pass

    @abstractmethod
    async def get_all_venues(self) -> list[Venue]:
        pass

    @abstractmethod
    async def add(self, venue: Venue) -> Venue:
        pass

    @abstractmethod
    async def update(self, updated_venue: Venue) -> Venue:
        pass

    @abstractmethod
    async def delete(self, venue_id: int) -> None:
        pass
