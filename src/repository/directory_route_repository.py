from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.icity_repository import ICityRepository
from abstract_repository.idirectory_route_repository import IDirectoryRouteRepository
from models.directory_route import DirectoryRoute


logger = logging.getLogger(__name__)


class DirectoryRouteRepository(IDirectoryRouteRepository):
    def __init__(self, session: AsyncSession, city_repo: ICityRepository):
        self.session = session
        self.city_repo = city_repo
        logger.debug("Инициализация DirectoryRouteRepository")

    async def get_list(self) -> list[DirectoryRoute]:
        query = text("SELECT * FROM directory_route ORDER by id")
        try:
            result = await self.session.execute(query)
            rows = result.mappings().all()
            d_routes = [
                DirectoryRoute(
                    d_route_id=row["id"],
                    type_transport=row["type_transport"],
                    cost=row["price"],
                    distance=row["distance"],
                    departure_city=await self.city_repo.get_by_id(
                        row["departure_city"]
                    ),
                    destination_city=await self.city_repo.get_by_id(
                        row["arrival_city"]
                    ),
                )
                for row in rows
            ]
            logger.debug("Успешно получено %d справочников", len(d_routes))
            return d_routes
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении списка справочников: %s", str(e), exc_info=True
            )
            return []

    async def get_by_id(self, directory_route_id: int) -> DirectoryRoute | None:
        query = text("SELECT * FROM directory_route WHERE id = :directory_route_id")
        try:
            result = await self.session.execute(
                query, {"directory_route_id": directory_route_id}
            )
            row = result.mappings().first()
            if row:
                departure_city = await self.city_repo.get_by_id(row["departure_city"])
                destination_city = await self.city_repo.get_by_id(row["arrival_city"])
                logger.debug("Найден справочник ID %d", directory_route_id)
                return DirectoryRoute(
                    d_route_id=row["id"],
                    type_transport=row["type_transport"],
                    cost=row["price"],
                    distance=row["distance"],
                    departure_city=departure_city,
                    destination_city=destination_city,
                )
            logger.warning("Справочник с ID %d не найден", directory_route_id)
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении справочника по ID %d: %s",
                directory_route_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, directory_route: DirectoryRoute) -> DirectoryRoute:
        query = text(
            """
            INSERT INTO directory_route (type_transport, price, distance, departure_city, arrival_city)
            VALUES (:type_transport, :price, :distance, :departure_city, :arrival_city)
            RETURNING id
        """
        )
        try:
            if (
                directory_route.departure_city is None
                or directory_route.destination_city is None
            ):
                logger.error("Отсутствуют данные о городах")
                raise
            row = await self.session.execute(
                query,
                {
                    "type_transport": directory_route.type_transport,
                    "price": directory_route.cost,
                    "distance": directory_route.distance,
                    "departure_city": directory_route.departure_city.city_id,
                    "arrival_city": directory_route.destination_city.city_id,
                },
            )
            new_id = row.scalar_one()
            await self.session.commit()
            logger.debug("Справочник успешно добавлен")
            directory_route.d_route_id = new_id
        except IntegrityError:
            logger.warning("Справочник уже существует в базе данных")
            await self.session.rollback()
        except SQLAlchemyError as e:
            logger.error("Ошибка при добавлении справочника: %s", str(e), exc_info=True)
            await self.session.rollback()
        return directory_route

    async def update(self, update_directory_route: DirectoryRoute) -> None:
        if (
            update_directory_route.departure_city is None
            or update_directory_route.destination_city is None
        ):
            logger.error("Отсутствуют данные о городах")
            return
        query = text(
            """
            UPDATE directory_route
            SET type_transport = :type_transport,
                price = :price,
                distance = :distance,
                departure_city = :departure_city,
                arrival_city = :arrival_city
            WHERE id = :directory_route_id
        """
        )
        try:
            await self.session.execute(
                query,
                {
                    "type_transport": update_directory_route.type_transport,
                    "price": update_directory_route.cost,
                    "distance": update_directory_route.distance,
                    "departure_city": update_directory_route.departure_city.city_id,
                    "arrival_city": update_directory_route.destination_city.city_id,
                    "directory_route_id": update_directory_route.d_route_id,
                },
            )
            await self.session.commit()
            logger.debug("Справочник успешно обновлен")
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при обновлении справочника маршрутов с ID %d: %s",
                str(e),
                exc_info=True,
            )

    async def delete(self, directory_route_id: int) -> None:
        query = text("DELETE FROM directory_route WHERE id = :directory_route_id")
        try:
            await self.session.execute(
                query, {"directory_route_id": directory_route_id}
            )
            await self.session.commit()
            logger.debug("Справочник ID %d успешно удален", directory_route_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении справочника маршрутов с ID %d: %s",
                directory_route_id,
                e,
            )

    async def get_by_cities(
        self, from_city_id: int, to_city_id: int, type_transport: str
    ) -> DirectoryRoute | None:
        query = text(
            """
            SELECT * FROM directory_route 
            WHERE departure_city = :from_id AND arrival_city = :to_id AND type_transport = :type_transport
        """
        )
        try:
            result = await self.session.execute(
                query,
                {
                    "from_id": from_city_id,
                    "to_id": to_city_id,
                    "type_transport": type_transport,
                },
            )
            row = result.mappings().first()
            if row:
                departure_city = await self.city_repo.get_by_id(row["departure_city"])
                destination_city = await self.city_repo.get_by_id(row["arrival_city"])
                logger.debug("Найден справочник ID %d", row["id"])
                return DirectoryRoute(
                    d_route_id=row["id"],
                    type_transport=type_transport,
                    cost=row["price"],
                    distance=row["distance"],
                    departure_city=departure_city,
                    destination_city=destination_city,
                )

            logger.warning(
                "Справочник маршрута между городами %d и %d не найден",
                from_city_id,
                to_city_id,
            )
            return None

        except SQLAlchemyError:
            logger.error("Ошибка при получении справочника маршрутов по городам")
        return None

    async def change_transport(
        self, d_route_id: int, new_transport: str
    ) -> DirectoryRoute | None:
        current_route = await self.get_by_id(d_route_id)
        if not current_route:
            logger.warning("Маршрут с ID %d не найден", d_route_id)
            return None
        if not current_route.departure_city or not current_route.destination_city:
            logger.warning("Города в маршруте с ID %d не найдены", d_route_id)
            return None

        return await self.get_by_cities(
            from_city_id=current_route.departure_city.city_id,
            to_city_id=current_route.destination_city.city_id,
            type_transport=new_transport,
        )
