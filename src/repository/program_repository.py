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
                start_venue = await self.venue_repo.get_by_id(row["start_venue"]) if row["start_venue"] else None
                end_venue = await self.venue_repo.get_by_id(row["end_venue"]) if row["end_venue"] else None
                programs.append(Program(
                    program_id=row["id"],
                    transfer_type=row["transfer_type"],
                    cost=row["cost"],
                    transfer_duration_minutes=row["transfer_duration_minutes"],
                    start_venue=start_venue,
                    end_venue=end_venue,
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
                start_venue = await self.venue_repo.get_by_id(row["start_venue"]) if row["start_venue"] else None
                end_venue = await self.venue_repo.get_by_id(row["end_venue"]) if row["end_venue"] else None
                logger.debug("Найдена программа ID %d", program_id)
                return Program(
                    program_id=row["id"],
                    transfer_type=row["transfer_type"],
                    cost=row["cost"],
                    transfer_duration_minutes=row["transfer_duration_minutes"],
                    start_venue=start_venue,
                    end_venue=end_venue,
                )
            logger.warning("Программа с ID %d не найдена", program_id)
            return None
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении программы по ID %d: %s", program_id, str(e), exc_info=True)
            return None

    async def add(self, program: Program) -> Program:
        query = text("""
            INSERT INTO program (transfer_type, start_venue, end_venue, transfer_duration_minutes, cost)
            VALUES (:transfer_type, :start_venue, :end_venue, :transfer_duration_minutes, :cost)
            RETURNING id
        """)
        try:
            result = await self.session.execute(query, {
                "transfer_type": program.transfer_type,
                "start_venue": program.start_venue.venue_id if program.start_venue else None,
                "end_venue": program.end_venue.venue_id if program.end_venue else None,
                "transfer_duration_minutes": program.transfer_duration_minutes,
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
            SET transfer_type = :transfer_type,
                start_venue = :start_venue,
                end_venue = :end_venue,
                transfer_duration_minutes = :transfer_duration_minutes,
                cost = :cost
            WHERE id = :program_id
        """)
        try:
            result = await self.session.execute(query, {
                "transfer_type": update_program.transfer_type,
                "start_venue": update_program.start_venue.venue_id if update_program.start_venue else None,
                "end_venue": update_program.end_venue.venue_id if update_program.end_venue else None,
                "transfer_duration_minutes": update_program.transfer_duration_minutes,
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
        self, start_venue_id: int, end_venue_id: int, transfer_type: str
    ) -> Program | None:
        query = text("""
            SELECT * FROM program
            WHERE start_venue = :from_id AND end_venue = :to_id AND transfer_type = :transfer_type
        """)
        try:
            result = await self.session.execute(query, {
                "from_id": start_venue_id,
                "to_id": end_venue_id,
                "transfer_type": transfer_type,
            })
            row = result.mappings().first()
            if row:
                start_venue = await self.venue_repo.get_by_id(row["start_venue"])
                end_venue = await self.venue_repo.get_by_id(row["end_venue"])
                logger.debug("Найдена программа ID %d", row["id"])
                return Program(
                    program_id=row["id"],
                    transfer_type=transfer_type,
                    cost=row["cost"],
                    transfer_duration_minutes=row["transfer_duration_minutes"],
                    start_venue=start_venue,
                    end_venue=end_venue,
                )
            logger.warning("Программа между площадками %d и %d не найдена", start_venue_id, end_venue_id)
            return None
        except SQLAlchemyError:
            logger.error("Ошибка при получении программы по площадкам")
        return None

    async def change_transfer_type(self, program_id: int, new_transfer_type: str) -> Program | None:
        current = await self.get_by_id(program_id)
        if not current:
            logger.warning("Программа с ID %d не найдена", program_id)
            return None
        if not current.start_venue or not current.end_venue:
            logger.warning("Площадки в программе с ID %d не найдены", program_id)
            return None
        return await self.get_by_venues(
            start_venue_id=current.start_venue.venue_id,
            end_venue_id=current.end_venue.venue_id,
            transfer_type=new_transfer_type,
        )
