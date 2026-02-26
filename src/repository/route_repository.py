from __future__ import annotations

import logging

from datetime import timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.idirectory_route_repository import IDirectoryRouteRepository
from abstract_repository.iroute_repository import IRouteRepository
from abstract_repository.itravel_repository import ITravelRepository
from models.directory_route import DirectoryRoute
from models.route import Route


logger = logging.getLogger(__name__)


class RouteRepository(IRouteRepository):
    def __init__(
        self,
        session: AsyncSession,
        d_route_repo: IDirectoryRouteRepository,
        travel_repo: ITravelRepository,
    ):
        self.session = session
        self.d_route_repo = d_route_repo
        self.travel_repo = travel_repo
        logger.debug("Инициализация RouteRepository")

    async def get_list(self) -> list[Route]:
        query = text("SELECT * FROM route")
        try:
            result = await self.session.execute(query)
            rows = [dict(row) for row in result.mappings()]
            routes = []
            for row in rows:
                route = Route(
                    route_id=row["id"],
                    d_route=await self.d_route_repo.get_by_id(row["d_route_id"]),
                    travels=await self.travel_repo.get_by_id(row["travel_id"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
                routes.append(route)
            logger.debug("Успешно получено %d маршрутов", len(routes))
            return routes
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении списка маршрутов: %s", str(e), exc_info=True
            )
            return []

    async def get_by_id(self, route_id: int) -> Route | None:
        query = text("SELECT * FROM route WHERE id = :route_id")
        try:
            result = await self.session.execute(query, {"route_id": route_id})
            row = result.mappings().first()
            if row:
                logger.debug("Найден маршрут ID %d", route_id)
                return Route(
                    route_id=row["id"],
                    d_route=await self.d_route_repo.get_by_id(row["d_route_id"]),
                    travels=await self.travel_repo.get_by_id(row["travel_id"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
            logger.warning("Маршрут с ID %d не найден", route_id)
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении маршрута по ID %d: %s",
                route_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, route: Route) -> Route:
        query = text(
            """
            INSERT INTO route (d_route_id, travel_id, start_time, end_time, type)
            VALUES (:d_route_id, :travel_id, :start_time, :end_time, :type)
            RETURNING id
        """
        )
        try:
            if route.travels is None:
                logger.error("Отсутствуют данные о путешествии")
                raise
            if route.d_route is None:
                logger.error("Отсутствуют данные о справочнике путешествий")
                raise
            row = await self.session.execute(
                query,
                {
                    "d_route_id": route.d_route.d_route_id,
                    "travel_id": route.travels.travel_id,
                    "start_time": route.start_time,
                    "end_time": route.end_time,
                    "type": route.type,
                },
            )
            new_id = row.scalar_one()
            await self.session.commit()
            logger.debug("Маршрут успешно добавлен")
            route.route_id = new_id
        except IntegrityError:
            await self.session.rollback()
            logger.warning("Маршрут уже существует в базе данных")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при добавлении маршрута: %s", str(e), exc_info=True)
        return route

    async def update(self, update_route: Route) -> None:
        if update_route.travels is None:
            logger.error("Отсутствуют данные о путешествии для обновления")
            return
        if update_route.d_route is None:
            logger.error("Отсутствуют данные о справочнике путешествий для обновления")
            return
        query = text(
            """
            UPDATE route
            SET d_route_id = :d_route_id,
            travel_id = :travel_id,
            start_time = :start_time,
            end_time = :end_time,
            type = :type
            WHERE id = :route_id
        """
        )
        try:
            await self.session.execute(
                query,
                {
                    "d_route_id": update_route.d_route.d_route_id,
                    "travel_id": update_route.travels.travel_id,
                    "start_time": update_route.start_time,
                    "end_time": update_route.end_time,
                    "route_id": update_route.route_id,
                    "type": update_route.type,
                },
            )
            await self.session.commit()
            logger.debug("Маршрут ID %d успешно обновлен", update_route.route_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при обновлении маршрута ID %d: %s",
                update_route.route_id,
                str(e),
                exc_info=True,
            )

    async def delete(self, route_id: int) -> None:
        query = text("DELETE FROM route WHERE id = :route_id")
        try:
            await self.session.execute(query, {"route_id": route_id})
            await self.session.commit()
            logger.debug("Маршрут ID %d успешно удален", route_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении маршрута ID %d: %s",
                route_id,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()

    async def get_routes_by_travel_id_ordered(self, travel_id: int) -> list[Route]:
        query = text(
            """
            SELECT * FROM route 
            WHERE travel_id = :travel_id
            ORDER BY start_time
        """
        )
        try:
            result = await self.session.execute(query, {"travel_id": travel_id})
            rows = result.mappings().all()
            routes = [
                Route(
                    route_id=row["id"],
                    d_route=await self.d_route_repo.get_by_id(row["d_route_id"]),
                    travels=await self.travel_repo.get_by_id(row["travel_id"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
                for row in rows
            ]
            logger.debug("Маршрут с travel ID %d успешно найден", travel_id)
            return routes
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении маршрута с travel ID %d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )
        return []

    async def get_routes_by_city(self, city_id: int) -> list[Route]:
        query = text(
            """
            SELECT * 
            FROM route r
            JOIN directory_route dr ON r.d_route_id = dr.id
            WHERE departure_city = :city_id OR arrival_city = :city_id
        """
        )
        try:
            result = await self.session.execute(query, {"city_id": city_id})
            rows = result.mappings().all()

            routes = [
                Route(
                    route_id=row["id"],
                    d_route=await self.d_route_repo.get_by_id(row["d_route_id"]),
                    travels=await self.travel_repo.get_by_id(row["travel_id"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
                for row in rows
            ]
            logger.debug("Маршрут с travel ID %d успешно найден", city_id)
            return routes
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении маршрута с city ID %d: %s",
                city_id,
                str(e),
                exc_info=True,
            )
            return []

    async def delete_city_from_route(self, travel_id: int, city_id: int) -> None:
        routes = await self.get_routes_by_travel_id_ordered(travel_id)
        if not routes:
            raise ValueError("Маршрут пуст")

        segments_to_remove = []
        for i, route in enumerate(routes):
            if route.d_route is None:
                continue

            if (
                route.d_route.departure_city
                and route.d_route.departure_city.city_id == city_id
            ) or (
                route.d_route.destination_city
                and route.d_route.destination_city.city_id == city_id
            ):
                segments_to_remove.append(i)

        if not segments_to_remove:
            raise ValueError(f"Город {city_id} не найден в маршруте")

        prev_city_id = None
        next_city_id = None

        first_segment_idx = segments_to_remove[0]
        if first_segment_idx > 0:
            prev_route = routes[first_segment_idx - 1]
            if (
                prev_route.d_route is not None
                and prev_route.d_route.departure_city is not None
            ):
                prev_city_id = prev_route.d_route.departure_city.city_id

        last_segment_idx = segments_to_remove[-1]
        if last_segment_idx < len(routes) - 1:
            next_route = routes[last_segment_idx + 1]
            if (
                next_route.d_route is not None
                and next_route.d_route.destination_city is not None
            ):
                next_city_id = next_route.d_route.destination_city.city_id

        for i in sorted(segments_to_remove, reverse=True):
            await self.delete(routes[i].route_id)

        if prev_city_id and next_city_id:
            first_removed_route = routes[segments_to_remove[0]]
            if first_removed_route.d_route is None:
                raise ValueError("Не удалось определить транспорт для нового сегмента")
            transport = first_removed_route.d_route.type_transport
            start_time = first_removed_route.start_time

            d_route = await self._get_d_route_between(
                prev_city_id, next_city_id, transport
            )
            new_route = Route(
                route_id=1,
                d_route=d_route,
                travels=routes[0].travels,
                start_time=start_time,
                end_time=start_time + timedelta(hours=2),
                type=routes[0].type,
            )
            await self.add(new_route)

    async def change_transport(
        self, d_route_id: int, route_id: int, new_transport: str
    ) -> Route | None:
        try:
            route_query = text(
                """
                SELECT * 
                FROM route 
                WHERE id = :route_id
            """
            )
            result = await self.session.execute(route_query, {"route_id": route_id})
            route = result.mappings().first()

            if not route:
                logger.error(
                    "Невозможно поменять транспорт, маршрут с ID %d не найден", route_id
                )
                return None

            new_d_route = await self.d_route_repo.change_transport(
                d_route_id, new_transport
            )
            if not new_d_route:
                logger.error(
                    "Справочник маршрута с ID %d и транспортом %s не найден",
                    d_route_id,
                    new_transport,
                )
                return None

            update_query = text(
                """
                UPDATE route
                SET d_route_id = :new_d_route_id
                WHERE id = :route_id
                RETURNING id
            """
            )
            result = await self.session.execute(
                update_query,
                {"new_d_route_id": new_d_route.d_route_id, "route_id": route_id},
            )
            await self.session.commit()
            new_id = result.scalar_one()
            logger.debug(
                "Транспорт %s в маршруте ID %d успешно обновлён",
                new_transport,
                route_id,
            )
            return await self.get_by_id(new_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при изменении транспорта маршрута с ID %d: %s",
                route_id,
                str(e),
                exc_info=True,
            )
            await self.session.rollback()
            raise

    async def _get_d_route_between(
        self, from_city_id: int, to_city_id: int, transport: str
    ) -> DirectoryRoute:
        d_route = await self.d_route_repo.get_by_cities(
            from_city_id, to_city_id, transport
        )
        if not d_route:
            raise ValueError(
                f"Нет маршрута между городами {from_city_id} и {to_city_id}"
            )
        return d_route

    async def insert_city_after(
        self, travel_id: int, new_city_id: int, after_city_id: int, transport: str
    ) -> None:
        routes = await self.get_routes_by_travel_id_ordered(travel_id)
        if not routes:
            raise ValueError("Маршрут пуст")

        target_route = None
        insert_after = False

        for route in routes:
            if route.d_route is None:
                continue

            dest_city = getattr(route.d_route, "destination_city", None) or getattr(
                route.d_route, "destination_city", None
            )
            dep_city = getattr(route.d_route, "departure_city", None)

            if dest_city and dest_city.city_id == after_city_id:
                target_route = route
                insert_after = True
                break
            if dep_city and dep_city.city_id == after_city_id:
                target_route = route
                break

        if target_route is None or target_route.d_route is None:
            raise ValueError(f"Город {after_city_id} не найден в маршруте")

        if insert_after:
            d_route_new = await self._get_d_route_between(
                after_city_id, new_city_id, transport
            )

            new_route = Route(
                route_id=1,
                d_route=d_route_new,
                travels=target_route.travels,
                start_time=target_route.end_time,
                end_time=target_route.end_time + timedelta(hours=2),
                type=target_route.type,
            )
            await self.add(new_route)
        else:
            d_route_new = await self._get_d_route_between(
                new_city_id, after_city_id, transport
            )

            target_route.d_route = d_route_new
            target_route.end_time = target_route.start_time + timedelta(hours=2)

        await self.session.commit()

    async def get_routes_by_user_and_status_and_type(
        self, user_id: int, status: str, type_route: str
    ) -> list[Route]:
        try:
            sql = text(
                """
                SELECT r.* 
                FROM route r
                JOIN travel t ON r.travel_id = t.id
                JOIN users_travel ut ON t.id = ut.travel_id
                WHERE ut.users_id = :user_id AND t.status = :status AND r.type = :type
            """
            )
            result = await self.session.execute(
                sql, {"user_id": user_id, "status": status, "type": type_route}
            )
            rows = result.mappings().all()

            routes = [
                Route(
                    route_id=row["id"],
                    d_route=await self.d_route_repo.get_by_id(row["d_route_id"]),
                    travels=await self.travel_repo.get_by_id(row["travel_id"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
                for row in rows
            ]
            logger.debug(
                "Найдено %d маршрутов для user_id=%d со статусом %s",
                len(routes),
                user_id,
                status,
            )
            return routes
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении маршрутов по user_id=%d и статусу %s: %s",
                user_id,
                status,
                str(e),
                exc_info=True,
            )
            raise

    async def get_routes_by_type(self, type_route: str) -> list[Route]:
        query = text(
            """
            SELECT * FROM route
            WHERE type = :type
        """
        )
        try:
            result = await self.session.execute(query, {"type": type_route})
            rows = result.mappings().all()

            routes = [
                Route(
                    route_id=row["id"],
                    d_route=await self.d_route_repo.get_by_id(row["d_route_id"]),
                    travels=await self.travel_repo.get_by_id(row["travel_id"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    type=row["type"],
                )
                for row in rows
            ]

            logger.debug("Найдено %d маршрутов с типом %s", len(routes), type_route)
            return routes
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении маршрутов с типом %s: %s",
                type_route,
                str(e),
                exc_info=True,
            )
            return []

    async def get_route_parts(self, travel_id: int) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT 
                r.id as route_id,
                dr.id as d_route_id,
                dc.city_id as departure_city_id,
                dc.name as departure_city_name,
                ac.city_id as arrival_city_id,
                ac.name as arrival_city_name,
                dr.type_transport as transport,
                dr.price as price,
                r.start_time,
                r.end_time,
                r.type
            FROM route r
            JOIN directory_route dr ON r.d_route_id = dr.id
            JOIN city dc ON dr.departure_city = dc.city_id
            JOIN city ac ON dr.arrival_city = ac.city_id
            WHERE r.travel_id = :travel_id
            ORDER BY r.start_time;
        """
        )

        try:
            result = await self.session.execute(query, {"travel_id": travel_id})
            route_parts = []

            for row in result.mappings():
                route_parts.append(
                    {
                        "route_id": row["route_id"],
                        "d_route_id": row["d_route_id"],
                        "departure_city": {
                            "city_id": row["departure_city_id"],
                            "name": row["departure_city_name"],
                        },
                        "destination_city": {
                            "city_id": row["arrival_city_id"],
                            "name": row["arrival_city_name"],
                        },
                        "transport": row["transport"],
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "type": row["type"],
                        "price": row["price"],
                    }
                )

            logger.debug(
                "Получено %d частей маршрута для travel_id=%d",
                len(route_parts),
                travel_id,
            )
            return route_parts

        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении частей маршрута для travel_id=%d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )
            raise
