from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.ilodging_repository import ILodgingRepository
from abstract_repository.ivenue_repository import IVenueRepository
from models.lodging import Lodging


logger = logging.getLogger(__name__)


class LodgingRepository(ILodgingRepository):
    def __init__(self, session: AsyncSession, venue_repo: IVenueRepository) -> None:
        self.session = session
        self.venue_repo = venue_repo
        logger.debug("Инициализация LodgingRepository")

    async def get_list(self) -> list[Lodging]:
        query = text("SELECT * FROM lodgings ORDER BY id")
        try:
            result = await self.session.execute(query)
            lodgings = []
            for row in result.mappings():
                venue = await self.venue_repo.get_by_id(row["Venue"]) if row["Venue"] else None
                lodgings.append(Lodging(
                    lodging_id=row["id"],
                    price=row["price"],
                    address=row["address"],
                    name=row["name"],
                    type=row["type"],
                    rating=row["rating"],
                    check_in=row["check_in"],
                    check_out=row["check_out"],
                    venue=venue,
                ))
            logger.debug("Успешно получено %d размещений", len(lodgings))
            return lodgings
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка размещений: %s", str(e), exc_info=True)
            raise

    async def get_by_id(self, lodging_id: int) -> Lodging | None:
        query = text("SELECT * FROM lodgings WHERE id = :lodging_id")
        try:
            result = await self.session.execute(query, {"lodging_id": lodging_id})
            row = result.mappings().first()
            if row:
                venue = await self.venue_repo.get_by_id(row["Venue"]) if row["Venue"] else None
                logger.debug("Найдено размещение ID %d: %s", lodging_id, row["name"])
                return Lodging(
                    lodging_id=row["id"],
                    price=row["price"],
                    address=row["address"],
                    name=row["name"],
                    type=row["type"],
                    rating=row["rating"],
                    check_in=row["check_in"],
                    check_out=row["check_out"],
                    venue=venue,
                )
            logger.warning("Размещение с ID %d не найдено", lodging_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении размещения по ID %d: %s", lodging_id, str(e), exc_info=True)
            return None

    async def add(self, lodging: Lodging) -> Lodging:
        query = text("""
            INSERT INTO lodgings (price, address, name, type, rating, check_in, check_out, Venue)
            VALUES (:price, :address, :name, :type, :rating, :check_in, :check_out, :venue)
            RETURNING id
        """)
        try:
            result = await self.session.execute(query, {
                "price": lodging.price,
                "address": lodging.address,
                "name": lodging.name,
                "type": lodging.type,
                "rating": lodging.rating,
                "check_in": lodging.check_in,
                "check_out": lodging.check_out,
                "venue": lodging.venue.venue_id if lodging.venue else None,
            })
            new_id = result.scalar_one()
            await self.session.commit()
            logger.debug("Размещение '%s' успешно добавлено", lodging.name)
            lodging.lodging_id = new_id
        except IntegrityError:
            logger.warning("Размещение '%s' уже существует", lodging.name)
            await self.session.rollback()
            raise ValueError("Размещение с таким названием уже существует")
        except SQLAlchemyError as e:
            logger.error("Ошибка при добавлении размещения '%s': %s", lodging.name, str(e), exc_info=True)
            await self.session.rollback()
            raise
        return lodging

    async def update(self, update_lodging: Lodging) -> None:
        query = text("""
            UPDATE lodgings
            SET price = :price,
                address = :address,
                name = :name,
                type = :type,
                rating = :rating,
                check_in = :check_in,
                check_out = :check_out,
                Venue = :venue
            WHERE id = :lodging_id
        """)
        try:
            result = await self.session.execute(query, {
                "price": update_lodging.price,
                "address": update_lodging.address,
                "name": update_lodging.name,
                "type": update_lodging.type,
                "rating": update_lodging.rating,
                "check_in": update_lodging.check_in,
                "check_out": update_lodging.check_out,
                "venue": update_lodging.venue.venue_id if update_lodging.venue else None,
                "lodging_id": update_lodging.lodging_id,
            })
            if result.rowcount == 0:
                raise ValueError(f"Размещение с ID {update_lodging.lodging_id} не найдено")
            await self.session.commit()
            logger.debug("Размещение ID %d успешно обновлено", update_lodging.lodging_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при обновлении размещения ID %d: %s", update_lodging.lodging_id, str(e), exc_info=True)
            raise

    async def delete(self, lodging_id: int) -> None:
        query = text("DELETE FROM lodgings WHERE id = :lodging_id")
        try:
            result = await self.session.execute(query, {"lodging_id": lodging_id})
            if result.rowcount == 0:
                raise ValueError(f"Размещение с ID {lodging_id} не найдено")
            await self.session.commit()
            logger.debug("Размещение ID %d успешно удалено", lodging_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при удалении размещения ID %d: %s", lodging_id, str(e), exc_info=True)
            raise
