from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from abstract_repository.iprogram_repository import IProgramRepository
from abstract_repository.ivenue_repository import IVenueRepository
from models.program import Program


logger = logging.getLogger(__name__)


class ProgramRepository(IProgramRepository):
    def __init__(self, session: AsyncSession, venue_repo: IVenueRepository) -> None:
        self.session = session
        self.venue_repo = venue_repo
        logger.debug("Инициализация ProgramRepository")

    async def get_list(self) -> list[Program]:
        query = text("SELECT * FROM program ORDER BY id")
        try:
            result = await self.session.execute(query)
            programs = []
            for row in result.mappings():
                from_venue = await self.venue_repo.get_by_id(row["from_venue"]) if row["from_venue"] else None
                to_venue = await self.venue_repo.get_by_id(row["to_venue"]) if row["to_venue"] else None
                programs.append(Program(
                    program_id=row["id"],
                    type_transport=row["type_transport"],
                    cost=row["cost"],
                    distance=row["distance"],
                    from_venue=from_venue,
                    to_venue=to_venue,
                ))
            logger.debug("Успешно получено %d программ", len(programs))
            return programs
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка программ: %s", str(e), exc_info=True)
            return []

    async def get_by_id(self, program_id: int) -> Program | None:
        query = text("SELECT * FROM program WHERE id = :program_id")
        try:
            result = await self.session.execute(query, {"program_id": program_id})
            row = result.mappings().first()
            if row:
                from_venue = await self.venue_repo.get_by_id(row["from_venue"]) if row["from_venue"] else None
                to_venue = await self.venue_repo.get_by_id(row["to_venue"]) if row["to_venue"] else None
                logger.debug("Найдена программа ID %d", program_id)
                return Program(
                    program_id=row["id"],
                    type_transport=row["type_transport"],
                    cost=row["cost"],
                    distance=row["distance"],
                    from_venue=from_venue,
                    to_venue=to_venue,
                )
            logger.warning("Программа с ID %d не найдена", program_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении программы по ID %d: %s", program_id, str(e), exc_info=True)
            return None

    async def add(self, program: Program) -> Program:
        query = text("""
            INSERT INTO program (type_transport, from_venue, to_venue, distance, cost)
            VALUES (:type_transport, :from_venue, :to_venue, :distance, :cost)
            RETURNING id
        """)
        try:
            result = await self.session.execute(query, {
                "type_transport": program.type_transport,
                "from_venue": program.from_venue.venue_id if program.from_venue else None,
                "to_venue": program.to_venue.venue_id if program.to_venue else None,
                "distance": program.distance,
                "cost": program.cost,
            })
            new_id = result.scalar_one()
            await self.session.commit()
            logger.debug("Программа успешно добавлена")
            program.program_id = new_id
        except IntegrityError:
            logger.warning("Программа уже существует")
            await self.session.rollback()
            raise ValueError("Программа с такими данными уже существует")
        except SQLAlchemyError as e:
            logger.error("Ошибка при добавлении программы: %s", str(e), exc_info=True)
            await self.session.rollback()
            raise
        return program

    async def update(self, update_program: Program) -> None:
        query = text("""
            UPDATE program
            SET type_transport = :type_transport,
                from_venue = :from_venue,
                to_venue = :to_venue,
                distance = :distance,
                cost = :cost
            WHERE id = :program_id
        """)
        try:
            result = await self.session.execute(query, {
                "type_transport": update_program.type_transport,
                "from_venue": update_program.from_venue.venue_id if update_program.from_venue else None,
                "to_venue": update_program.to_venue.venue_id if update_program.to_venue else None,
                "distance": update_program.distance,
                "cost": update_program.cost,
                "program_id": update_program.program_id,
            })
            if result.rowcount == 0:
                raise ValueError(f"Программа с ID {update_program.program_id} не найдена")
            await self.session.commit()
            logger.debug("Программа ID %d успешно обновлена", update_program.program_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при обновлении программы ID %d: %s", update_program.program_id, str(e), exc_info=True)
            raise

    async def delete(self, program_id: int) -> None:
        query = text("DELETE FROM program WHERE id = :program_id")
        try:
            result = await self.session.execute(query, {"program_id": program_id})
            if result.rowcount == 0:
                raise ValueError(f"Программа с ID {program_id} не найдена")
            await self.session.commit()
            logger.debug("Программа ID %d успешно удалена", program_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Ошибка при удалении программы ID %d: %s", program_id, str(e), exc_info=True)
            raise

    async def get_by_venues(
        self, from_venue_id: int, to_venue_id: int, type_transport: str
    ) -> Program | None:
        query = text("""
            SELECT * FROM program
            WHERE from_venue = :from_id AND to_venue = :to_id AND type_transport = :type_transport
        """)
        try:
            result = await self.session.execute(query, {
                "from_id": from_venue_id,
                "to_id": to_venue_id,
                "type_transport": type_transport,
            })
            row = result.mappings().first()
            if row:
                from_venue = await self.venue_repo.get_by_id(row["from_venue"])
                to_venue = await self.venue_repo.get_by_id(row["to_venue"])
                logger.debug("Найдена программа ID %d", row["id"])
                return Program(
                    program_id=row["id"],
                    type_transport=type_transport,
                    cost=row["cost"],
                    distance=row["distance"],
                    from_venue=from_venue,
                    to_venue=to_venue,
                )
            logger.warning("Программа между площадками %d и %d не найдена", from_venue_id, to_venue_id)
            return None
        except SQLAlchemyError:
            logger.error("Ошибка при получении программы по площадкам")
        return None

    async def change_transport(self, program_id: int, new_transport: str) -> Program | None:
        current = await self.get_by_id(program_id)
        if not current:
            logger.warning("Программа с ID %d не найдена", program_id)
            return None
        if not current.from_venue or not current.to_venue:
            logger.warning("Площадки в программе с ID %d не найдены", program_id)
            return None
        return await self.get_by_venues(
            from_venue_id=current.from_venue.venue_id,
            to_venue_id=current.to_venue.venue_id,
            type_transport=new_transport,
        )
