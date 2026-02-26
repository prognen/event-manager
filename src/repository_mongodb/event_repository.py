from __future__ import annotations

import logging

from typing import Any

from bson import Int64
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pymongo.errors import PyMongoError

from abstract_repository.iactivity_repository import IActivityRepository
from abstract_repository.ilodging_repository import ILodgingRepository
from abstract_repository.ievent_repository import IEventRepository
from abstract_repository.iuser_repository import IUserRepository
from models.activity import Activity
from models.lodging import Lodging
from models.event import Event
from models.user import User


logger = logging.getLogger(__name__)


class EventRepository(IEventRepository):
    def __init__(
        self,
        client: AsyncIOMotorClient[Any],
        user_repo: IUserRepository,
        activity_repo: IActivityRepository,
        lodging_repo: ILodgingRepository,
    ):
        self.db: AsyncIOMotorDatabase[Any] = client["event_db"]
        self.events = self.db["events"]
        self.user_repo = user_repo
        self.activity_repo = activity_repo
        self.lodging_repo = lodging_repo
        logger.debug("Инициализация EventRepository для MongoDB")

    async def get_lodgings_by_event(self, event_id: int) -> list[Lodging]:
        try:
            event = await self.events.find_one({"_id": event_id})
            if not event:
                return []

            lodgings = []
            for lodging_id in event.get("lodgings", []):
                lodging = await self.lodging_repo.get_by_id(int(lodging_id))
                if lodging:
                    lodgings.append(lodging)

            logger.debug(
                "Получено %d размещений для мероприятия ID %d",
                len(lodgings),
                event_id,
            )
            return lodgings
        except PyMongoError as e:
            logger.error("Ошибка при получении размещений: %s", str(e), exc_info=True)
            return []

    async def get_users_by_event(self, event_id: int) -> list[User]:
        try:
            event = await self.events.find_one({"_id": event_id})
            if not event:
                return []

            users = []
            for user_id in event.get("users", []):
                user = await self.user_repo.get_by_id(user_id)
                if user:
                    users.append(user)

            logger.debug(
                "Получено %d участников для мероприятия ID %d", len(users), event_id
            )
            return users
        except PyMongoError as e:
            logger.error(
                "Ошибка при получении участников: %s", str(e), exc_info=True
            )
            return []

    async def get_activities_by_event(self, event_id: int) -> list[Activity]:
        try:
            event = await self.events.find_one({"_id": event_id})
            if not event:
                return []

            activities = []
            for activity_id in event.get("activities", []):
                activity = await self.activity_repo.get_by_id(activity_id)
                if activity:
                    activities.append(activity)

            logger.debug(
                "Получено %d активностей для мероприятия ID %d",
                len(activities),
                event_id,
            )
            return activities
        except PyMongoError as e:
            logger.error("Ошибка при получении активностей: %s", str(e), exc_info=True)
            return []

    async def get_list(self) -> list[Event]:
        try:
            events = []
            async for doc in self.events.find().sort("_id"):
                events.append(
                    Event(
                        event_id=int(doc["_id"]),
                        status=doc["status"],
                        users=await self.get_users_by_event(int(doc["_id"])),
                        activities=await self.get_activities_by_event(
                            int(doc["_id"])
                        ),
                        lodgings=await self.get_lodgings_by_event(
                            int(doc["_id"])
                        ),
                    )
                )
            logger.debug("Получено %d записей о мероприятиях", len(events))
            return events
        except PyMongoError as e:
            logger.error("Ошибка при получении списка: %s", str(e), exc_info=True)
            return []

    async def get_event_by_session_id(self, session_id: int) -> Event | None:
        try:
            session = await self.db["sessions"].find_one({"_id": session_id})
            if not session:
                return None

            event = await self.events.find_one({"_id": session["event"]["_id"]})
            if not event:
                return None

            logger.debug("Мероприятие с session ID %d успешно найдено", session_id)
            return Event(
                event_id=event["_id"],
                status=event["status"],
                users=await self.get_users_by_event(event["_id"]),
                activities=await self.get_activities_by_event(event["_id"]),
                lodgings=await self.get_lodgings_by_event(event["_id"]),
            )
        except PyMongoError as e:
            logger.error("Ошибка при поиске по session ID: %s", str(e), exc_info=True)
            return None

    async def get_by_id(self, event_id: int) -> Event | None:
        try:
            event = await self.events.find_one({"_id": event_id})
            if not event:
                return None

            logger.debug("Найдено мероприятие ID %d", event_id)
            return Event(
                event_id=event["_id"],
                status=event["status"],
                users=await self.get_users_by_event(event_id),
                activities=await self.get_activities_by_event(event_id),
                lodgings=await self.get_lodgings_by_event(event_id),
            )
        except PyMongoError as e:
            logger.error("Ошибка при получении по ID: %s", str(e), exc_info=True)
            return None

    async def add(self, event: Event) -> Event:
        try:
            last_id = await self.events.find().sort("_id", -1).limit(1).next()
            new_id = Int64(last_id["_id"] + 1) if last_id else Int64(1)
            doc = {
                "_id": int(new_id),
                "status": event.status,
                "users": [user.user_id for user in event.users],
                "activities": [
                    act.activity_id for act in event.activities
                ],
                "lodgings": [
                    lodging.lodging_id for lodging in event.lodgings
                ],
            }

            result = await self.events.insert_one(doc)
            event.event_id = result.inserted_id
            logger.debug("Мероприятие создано с ID %s", str(result.inserted_id))
            return event
        except DuplicateKeyError:
            logger.warning("Дублирующаяся запись о мероприятии")
            return event
        except PyMongoError as e:
            logger.error("Ошибка при добавлении: %s", str(e), exc_info=True)
            return event

    async def update(self, update_event: Event) -> None:
        try:
            result = await self.events.update_one(
                {"_id": update_event.event_id},
                {
                    "$set": {
                        "status": update_event.status,
                        "users": (
                            [user.user_id for user in update_event.users]
                            if update_event.users
                            else []
                        ),
                        "activities": (
                            [
                                act.activity_id
                                for act in update_event.activities
                            ]
                            if update_event.activities
                            else []
                        ),
                        "lodgings": (
                            [
                                lodging.lodging_id
                                for lodging in update_event.lodgings
                            ]
                            if update_event.lodgings
                            else []
                        ),
                    }
                },
            )

            if result.modified_count == 0:
                logger.warning(
                    "Мероприятие ID %d не найдено для обновления",
                    update_event.event_id,
                )
            else:
                logger.debug(
                    "Мероприятие ID %d успешно обновлено", update_event.event_id
                )
        except PyMongoError as e:
            logger.error("Ошибка при обновлении: %s", str(e), exc_info=True)

    async def delete(self, event_id: int) -> None:
        try:
            result = await self.events.delete_one({"_id": event_id})
            if result.deleted_count == 0:
                logger.warning("Мероприятие ID %d не найдено для удаления", event_id)
            else:
                logger.debug("Мероприятие ID %d удалено", event_id)
        except PyMongoError as e:
            logger.error("Ошибка при удалении: %s", str(e), exc_info=True)

    async def search(self, event_dict: dict[str, Any]) -> list[Event]:
        try:
            query = {"status": {"$ne": "Завершено"}}

            if "start_time" in event_dict:
                query["sessions.start_time"] = {"$gte": event_dict["start_time"]}

            if "end_time" in event_dict:
                query["sessions.end_time"] = {"$lte": event_dict["end_time"]}

            if "from_venue" in event_dict:
                query["sessions.program.from_venue_id"] = event_dict["from_venue"]

            if "to_venue" in event_dict:
                query["sessions.program.to_venue_id"] = event_dict["to_venue"]

            if "activity_type" in event_dict:
                query["activities.activity_type"] = {
                    "$regex": event_dict["activity_type"],
                    "$options": "i",
                }

            events = []
            async for doc in self.events.find(query):
                events.append(
                    Event(
                        event_id=int(doc["_id"]),
                        status=doc["status"],
                        users=await self.get_users_by_event(int(doc["_id"])),
                        activities=await self.get_activities_by_event(
                            int(doc["_id"])
                        ),
                        lodgings=await self.get_lodgings_by_event(
                            int(doc["_id"])
                        ),
                    )
                )

            logger.debug("Успешно найдено %d мероприятий с параметрами", len(events))
            return events
        except PyMongoError as e:
            logger.error("Ошибка при поиске: %s", str(e), exc_info=True)
            return []

    async def complete(self, event_id: int) -> None:
        try:
            result = await self.events.update_one(
                {"_id": event_id}, {"$set": {"status": "Завершено"}}
            )

            if result.modified_count == 0:
                logger.warning("Мероприятие ID %d не найдено для завершения", event_id)
            else:
                logger.debug("Мероприятие ID %d успешно завершено", event_id)
        except PyMongoError as e:
            logger.error("Ошибка при завершении: %s", str(e), exc_info=True)

    async def link_activities(
        self, event_id: int, activity_ids: list[int]
    ) -> None:
        try:
            result = await self.events.update_one(
                {"_id": event_id}, {"$set": {"activities": activity_ids}}
            )

            if result.modified_count == 0:
                logger.warning("Мероприятие ID %d не найдено", event_id)
            else:
                logger.debug("Успешно связаны активности с мероприятием")
        except PyMongoError as e:
            logger.error("Ошибка при связывании активностей: %s", str(e), exc_info=True)
            raise

    async def link_lodgings(
        self, event_id: int, lodging_ids: list[int]
    ) -> None:
        try:
            result = await self.events.update_one(
                {"_id": event_id}, {"$set": {"lodgings": lodging_ids}}
            )

            if result.modified_count == 0:
                logger.warning("Мероприятие ID %d не найдено", event_id)
            else:
                logger.debug("Успешно связаны размещения с мероприятием")
        except PyMongoError as e:
            logger.error("Ошибка при связывании размещений: %s", str(e), exc_info=True)
            raise

    async def get_events_for_user(self, user_id: int, status: str) -> list[Event]:
        try:
            events = []
            async for doc in self.events.find({"status": status, "users": user_id}):
                events.append(
                    Event(
                        event_id=int(doc["_id"]),
                        status=doc["status"],
                        users=await self.get_users_by_event(int(doc["_id"])),
                        activities=await self.get_activities_by_event(
                            int(doc["_id"])
                        ),
                        lodgings=await self.get_lodgings_by_event(
                            int(doc["_id"])
                        ),
                    )
                )

            logger.debug(
                "Успешно найдены мероприятия по user_id = %d, status = %s",
                user_id,
                status,
            )
            return events
        except PyMongoError as e:
            logger.error("Ошибка при поиске: %s", str(e), exc_info=True)
            return []

    async def link_users(self, event_id: int, user_ids: list[int]) -> None:
        try:
            result = await self.events.update_one(
                {"_id": event_id}, {"$set": {"users": user_ids}}
            )

            if result.modified_count == 0:
                logger.warning("Мероприятие ID %d не найдено", event_id)
            else:
                logger.debug("Успешно связаны участники с мероприятием")
        except PyMongoError as e:
            logger.error(
                "Ошибка при связывании участников: %s", str(e), exc_info=True
            )
            raise
