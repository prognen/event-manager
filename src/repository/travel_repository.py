from __future__ import annotations

import logging

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.iaccommodation_repository import IAccommodationRepository
from abstract_repository.ientertainment_repository import IEntertainmentRepository
from abstract_repository.itravel_repository import ITravelRepository
from abstract_repository.iuser_repository import IUserRepository
from models.accommodation import Accommodation
from models.entertainment import Entertainment
from models.travel import Travel
from models.user import User


logger = logging.getLogger(__name__)


class TravelRepository(ITravelRepository):
    def __init__(
        self,
        session: AsyncSession,
        user_repo: IUserRepository,
        e_repo: IEntertainmentRepository,
        a_repo: IAccommodationRepository,
    ):
        self.session = session
        self.user_repo = user_repo
        self.entertainment_repo = e_repo
        self.accommodation_repo = a_repo
        logger.debug("Инициализация TravelRepository")

    async def get_accommodations_by_travel(self, travel_id: int) -> list[Accommodation]:
        query = text(
            "SELECT accommodation_id FROM travel_accommodations WHERE travel_id = :travel_id"
        )
        try:
            result = await self.session.execute(query, {"travel_id": travel_id})
            rows = result.fetchall()

            end_list = []
            for row in rows:
                acc = await self.accommodation_repo.get_by_id(row[0])
                if acc is not None:
                    end_list.append(acc)
            logger.debug(
                "Получено %d размещений для путешествия ID %d", len(end_list), travel_id
            )
            return end_list
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении размещений для путешествия ID %d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )
            return []

    async def get_users_by_travel(self, travel_id: int) -> list[User]:
        query = text(
            """
            SELECT users_id FROM users_travel 
            WHERE travel_id = :travel_id
        """
        )
        try:
            result = await self.session.execute(query, {"travel_id": travel_id})
            user_ids = [row[0] for row in result.fetchall()]

            users = []
            for user_id in user_ids:
                user = await self.user_repo.get_by_id(user_id)
                if user:
                    users.append(user)
            logger.debug(
                "Получено %d пользователей для путешествия ID %d", len(users), travel_id
            )
            return users
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении пользователей для путешествия ID %d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )
            return []

    async def get_entertainments_by_travel(self, travel_id: int) -> list[Entertainment]:
        query = text(
            "SELECT entertainment_id FROM travel_entertainment WHERE travel_id = :travel_id"
        )
        try:
            result = await self.session.execute(query, {"travel_id": travel_id})
            rows = result.fetchall()

            ent_list = []
            for row in rows:
                ent = await self.entertainment_repo.get_by_id(row[0])
                if ent is not None:
                    ent_list.append(ent)
            logger.debug(
                "Получено %d развлечений для путешествия ID %d",
                len(ent_list),
                travel_id,
            )
            return ent_list
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении развлечений для путешествия ID %d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )
            return []

    async def get_list(self) -> list[Travel]:
        query = text("SELECT * FROM travel ORDER BY id")
        try:
            result = await self.session.execute(query)
            rows = result.mappings()
            travels = []
            for row in rows:
                users = await self.get_users_by_travel(row["id"])
                if not users:
                    logger.warning(
                        "Пропущено путешествие %d: нет пользователей", row["id"]
                    )
                    continue

                entertainments = (
                    await self.get_entertainments_by_travel(row["id"]) or []
                )
                accommodations = (
                    await self.get_accommodations_by_travel(row["id"]) or []
                )

                travels.append(
                    Travel(
                        travel_id=row["id"],
                        status=row["status"],
                        users=users,
                        entertainments=entertainments,
                        accommodations=accommodations,
                    )
                )

            logger.debug("Получено %d записей о путешествиях", len(travels))
            return travels
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении списка путешествий: %s", str(e), exc_info=True
            )
            return []

    async def get_travel_by_route_id(self, route_id: int) -> Travel | None:
        query = text(
            """
            SELECT travel_id FROM route
            WHERE id = :route_id
        """
        )
        try:
            result = await self.session.execute(query, {"route_id": route_id})
            row = result.mappings().first()
            if row:
                travel = await self.get_by_id(row["travel_id"])
                logger.debug("Путешествие с route ID %d успешно найдено", route_id)
                return travel
            logger.warning("Путешествие по route ID %d не найдено", route_id)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении путешествия по route ID %d: %s",
                route_id,
                str(e),
                exc_info=True,
            )
        return None

    async def get_by_id(self, travel_id: int) -> Travel | None:
        query = text("SELECT * FROM travel WHERE id = :travel_id")
        try:
            result = await self.session.execute(query, {"travel_id": travel_id})
            row = result.mappings().first()
            if row:
                logger.debug("Найдено путешествие ID %d", travel_id)
                us = await self.get_users_by_travel(row["id"])
                if us == []:
                    return None
                return Travel(
                    travel_id=row["id"],
                    status=row["status"],
                    users=us,
                    entertainments=await self.get_entertainments_by_travel(row["id"]),
                    accommodations=await self.get_accommodations_by_travel(row["id"]),
                )
            logger.warning("Путешествие ID %d не найдено", travel_id)
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении путешествия по ID %d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )
            return None

    async def add(self, travel: Travel) -> Travel:
        query = text(
            """
            INSERT INTO travel (status)
            VALUES (:status)
            RETURNING id
        """
        )
        entertainment_query = text(
            """
            INSERT INTO travel_entertainment (travel_id, entertainment_id)
            VALUES (:travel_id, :entertainment_id)
        """
        )

        accommodation_query = text(
            """
            INSERT INTO travel_accommodations (travel_id, accommodation_id)
            VALUES (:travel_id, :accommodation_id)
        """
        )
        user_query = text(
            """
            INSERT INTO users_travel (users_id, travel_id) 
            VALUES (:users_id, :travel_id)
        """
        )
        try:
            result = await self.session.execute(query, {"status": travel.status})
            travel_id = result.scalar_one()
            logger.debug("Путешествие создано с ID %d", travel_id)
            travel.travel_id = travel_id
            if travel.users:
                for user in travel.users:
                    try:
                        await self.session.execute(
                            user_query,
                            {"users_id": user.user_id, "travel_id": travel_id},
                        )
                    except SQLAlchemyError as e:
                        raise ValueError(
                            f"Ошибка при добавлении пользователя с ID {user.user_id}: {e}"
                        )
            if travel.entertainments:
                for ent in travel.entertainments:
                    try:
                        await self.session.execute(
                            entertainment_query,
                            {
                                "travel_id": travel_id,
                                "entertainment_id": ent.entertainment_id,
                            },
                        )
                    except SQLAlchemyError as e:
                        raise ValueError(
                            f"Ошибка при добавлении развлечения с ID {ent.entertainment_id}: {e}"
                        )

            if travel.accommodations:
                for acc in travel.accommodations:
                    try:
                        await self.session.execute(
                            accommodation_query,
                            {
                                "travel_id": travel_id,
                                "accommodation_id": acc.accommodation_id,
                            },
                        )
                    except SQLAlchemyError as e:
                        raise ValueError(
                            f"Ошибка при добавлении размещения с ID {acc.accommodation_id}: {e}"
                        )

            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            logger.warning("Дублирующаяся запись о путешествии")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при добавлении путешествия: %s", str(e), exc_info=True)
        return travel

    async def update(self, update_travel: Travel) -> None:
        if update_travel.users is None:
            logger.warning("Нет данных пользователя для обновления путешествия")
            return
        check_query = text(
            """
            SELECT 1 FROM travel WHERE id = :travel_id
        """
        )
        update_travel_query = text(
            """
            UPDATE travel
            SET status = :status
            WHERE id = :travel_id
        """
        )
        delete_users_query = text(
            """
            DELETE FROM users_travel WHERE travel_id = :travel_id
        """
        )
        delete_entertainments_query = text(
            """
            DELETE FROM travel_entertainment WHERE travel_id = :travel_id
        """
        )

        delete_accommodations_query = text(
            """
            DELETE FROM travel_accommodations WHERE travel_id = :travel_id
        """
        )
        user_query = text(
            """
            INSERT INTO users_travel (users_id, travel_id)
            VALUES (:users_id, :travel_id)
        """
        )
        entertainment_query = text(
            """
            INSERT INTO travel_entertainment (travel_id, entertainment_id)
            VALUES (:travel_id, :entertainment_id)
        """
        )

        accommodation_query = text(
            """
            INSERT INTO travel_accommodations (travel_id, accommodation_id)
            VALUES (:travel_id, :accommodation_id)
        """
        )

        try:
            result = await self.session.execute(
                check_query, {"travel_id": update_travel.travel_id}
            )
            if result.fetchone() is None:
                logger.warning(
                    "Путешествие ID %d не существует для обновления",
                    update_travel.travel_id,
                )
                return
            await self.session.execute(
                update_travel_query,
                {"status": update_travel.status, "travel_id": update_travel.travel_id},
            )

            await self.session.execute(
                delete_entertainments_query, {"travel_id": update_travel.travel_id}
            )
            await self.session.execute(
                delete_accommodations_query, {"travel_id": update_travel.travel_id}
            )
            await self.session.execute(
                delete_users_query, {"travel_id": update_travel.travel_id}
            )
            if update_travel.users:
                for user in update_travel.users:
                    try:
                        await self.session.execute(
                            user_query,
                            {
                                "users_id": user.user_id,
                                "travel_id": update_travel.travel_id,
                            },
                        )
                    except SQLAlchemyError as e:
                        logger.error(
                            "Ошибка при добавлении пользователя с ID %d: %s",
                            user.user_id,
                            e,
                        )
            if update_travel.entertainments:
                for ent in update_travel.entertainments:
                    try:
                        await self.session.execute(
                            entertainment_query,
                            {
                                "travel_id": update_travel.travel_id,
                                "entertainment_id": ent.entertainment_id,
                            },
                        )
                    except SQLAlchemyError as e:
                        logger.error(
                            "Ошибка при добавлении развлечения с ID %d: %s",
                            ent.entertainment_id,
                            e,
                        )

            if update_travel.accommodations:
                for acc in update_travel.accommodations:
                    try:
                        await self.session.execute(
                            accommodation_query,
                            {
                                "travel_id": update_travel.travel_id,
                                "accommodation_id": acc.accommodation_id,
                            },
                        )
                    except SQLAlchemyError as e:
                        logger.error(
                            "Ошибка при добавлении размещения с ID %d: %s",
                            acc.accommodation_id,
                            e,
                        )
            await self.session.commit()
            logger.debug("Путешествие ID %d успешно обновлено", update_travel.travel_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при обновлении путешествия ID %d: %s",
                update_travel.travel_id,
                str(e),
                exc_info=True,
            )

    async def delete(self, travel_id: int) -> None:
        delete_users_query = text(
            """
            DELETE FROM users_travel WHERE travel_id = :travel_id
        """
        )
        delete_entertainments_query = text(
            """
            DELETE FROM travel_entertainment WHERE travel_id = :travel_id
        """
        )

        delete_accommodations_query = text(
            """
            DELETE FROM travel_accommodations WHERE travel_id = :travel_id
        """
        )

        query = text("DELETE FROM travel WHERE id = :travel_id")
        try:
            await self.session.execute(delete_users_query, {"travel_id": travel_id})
            await self.session.execute(
                delete_entertainments_query, {"travel_id": travel_id}
            )
            await self.session.execute(
                delete_accommodations_query, {"travel_id": travel_id}
            )
            await self.session.execute(query, {"travel_id": travel_id})
            await self.session.commit()
            logger.debug("Путешествие ID %d удалено", travel_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при удалении путешествия ID %d: %s",
                travel_id,
                str(e),
                exc_info=True,
            )

    async def search(self, travel_dict: dict[str, Any]) -> list[Travel]:
        sql = """ SELECT DISTINCT t.* 
            FROM travel t 
            JOIN route r ON t.id = r.travel_id 
            JOIN directory_route dr ON r.d_route_id = dr.id 
            LEFT JOIN travel_entertainment te ON t.id = te.travel_id 
            LEFT JOIN entertainment e ON te.entertainment_id = e.id 
            WHERE t.status != 'Завершен' 
        """
        params = {}
        if "start_time" in travel_dict:
            sql += " AND r.start_time >= :start_time"
            params["start_time"] = travel_dict["start_time"]

        if "end_time" in travel_dict:
            sql += " AND r.end_time <= :end_time"
            params["end_time"] = travel_dict["end_time"]

        if "departure_city" in travel_dict:
            sql += " AND dr.departure_city = :departure_city"
            params["departure_city"] = travel_dict["departure_city"]

        if "arrival_city" in travel_dict:
            sql += " AND dr.arrival_city = :arrival_city"
            params["arrival_city"] = travel_dict["arrival_city"]

        if "entertainment_name" in travel_dict:
            sql += " AND e.name ILIKE :entertainment_name"
            params["entertainment_name"] = f"%{travel_dict['entertainment_name']}%"
        try:
            result = await self.session.execute(text(sql), params)
            rows = result.mappings().all()
            travels = []
            for row in rows:
                travel = Travel(
                    travel_id=row["id"],
                    status=row["status"],
                    users=await self.get_users_by_travel(row["id"]),
                    entertainments=await self.get_entertainments_by_travel(row["id"]),
                    accommodations=await self.get_accommodations_by_travel(row["id"]),
                )
                travels.append(travel)
            logger.debug("Успешно найдено путешествие с параметрами: %s", params)
            return travels
        except SQLAlchemyError as e:
            logger.error("Ошибка при поиске путешествия: %s", str(e), exc_info=True)
            return []

    async def complete(self, travel_id: int) -> None:
        try:
            sql = """UPDATE travel
                    SET status = 'Завершен'
                    WHERE id = :travel_id"""
            await self.session.execute(text(sql), {"travel_id": travel_id})
            await self.session.commit()
            logger.debug("Путешествие ID %d успешно завершено", travel_id)
        except SQLAlchemyError:
            logger.debug("Ошибка при завершении путешествия ID %d", travel_id)
            await self.session.rollback()

    async def link_entertainments(
        self, travel_id: int, entertainment_ids: list[int]
    ) -> None:
        try:
            await self.session.execute(
                text("DELETE FROM travel_entertainment WHERE travel_id = :travel_id"),
                {"travel_id": travel_id},
            )

            for entertainment_id in entertainment_ids:
                await self.session.execute(
                    text(
                        """
                        INSERT INTO travel_entertainment (travel_id, entertainment_id)
                        VALUES (:travel_id, :entertainment_id)
                    """
                    ),
                    {"travel_id": travel_id, "entertainment_id": entertainment_id},
                )

            await self.session.commit()
            logger.debug("Успешно связаны развлечения с путешествием")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при связывании развлечений: %s", str(e), exc_info=True)
            raise

    async def link_accommodations(
        self, travel_id: int, accommodation_ids: list[int]
    ) -> None:
        try:
            await self.session.execute(
                text("DELETE FROM travel_accommodations WHERE travel_id = :travel_id"),
                {"travel_id": travel_id},
            )

            for accommodation_id in accommodation_ids:
                await self.session.execute(
                    text(
                        """
                        INSERT INTO travel_accommodations (travel_id, accommodation_id)
                        VALUES (:travel_id, :accommodation_id)
                    """
                    ),
                    {"travel_id": travel_id, "accommodation_id": accommodation_id},
                )

            await self.session.commit()
            logger.debug("Успешно связаны размещения с путешествием")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при связывании размещений: %s", str(e), exc_info=True)
            raise

    async def get_travels_for_user(self, user_id: int, status: str) -> list[Travel]:
        try:
            sql = """SELECT t.*
                    FROM travel t
                    JOIN users_travel ut ON ut.travel_id = t.id
                    WHERE t.status = :status AND ut.users_id = :user_id"""
            result = await self.session.execute(
                text(sql), {"user_id": user_id, "status": status}
            )
            rows = result.fetchall()
            travels = []
            for row in rows:
                travel = Travel(
                    travel_id=row.id,
                    status=status,
                    users=await self.get_users_by_travel(row.id),
                    entertainments=await self.get_entertainments_by_travel(row.id),
                    accommodations=await self.get_accommodations_by_travel(row.id),
                )
                travels.append(travel)
            logger.debug(
                "Успешно найдены путешествия по user_id = %d, status = %s",
                user_id,
                status,
            )
            return travels
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при поиске %s путешествий: %s", status, str(e), exc_info=True
            )
            return []

    async def link_users(self, travel_id: int, user_ids: list[int]) -> None:
        try:
            await self.session.execute(
                text("DELETE FROM users_travel WHERE travel_id = :travel_id"),
                {"travel_id": travel_id},
            )

            for user_id in user_ids:
                await self.session.execute(
                    text(
                        """
                        INSERT INTO users_travel (users_id, travel_id)
                        VALUES (:users_id, :travel_id)
                    """
                    ),
                    {"users_id": user_id, "travel_id": travel_id},
                )

            await self.session.commit()
            logger.debug("Успешно связаны пользователи с путешествием")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при связывании пользователей: %s", str(e), exc_info=True
            )
            raise
