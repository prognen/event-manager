from __future__ import annotations

import re

from unittest.mock import Mock

import pytest

from models.program import Program
from services.program_service import ProgramService


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_should_successfull_get_existed_program_by_id(mock_repo: Mock) -> None:
    program = Program(
        program_id=1,
        transfer_type="Самолет",
        cost=25866,
        transfer_duration_minutes=300000,
        start_venue=None,
        end_venue=None,
    )
    mock_repo.get_by_id.return_value = program
    service = ProgramService(mock_repo)

    result = await service.get_by_id(1)

    assert result == program
    mock_repo.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_get_not_existed_program(
    mock_repo: Mock,
) -> None:
    mock_repo.get_by_id.side_effect = ValueError("Not found")
    service = ProgramService(mock_repo)

    with pytest.raises(ValueError):
        await service.get_by_id(123)


@pytest.mark.asyncio
async def test_should_successfull_get_list(mock_repo: Mock) -> None:
    programs = [
        Program(
            program_id=1,
            transfer_type="Самолет",
            cost=100,
            transfer_duration_minutes=200,
            start_venue=None,
            end_venue=None,
        ),
        Program(
            program_id=2,
            transfer_type="Поезд",
            cost=50,
            transfer_duration_minutes=300,
            start_venue=None,
            end_venue=None,
        ),
    ]
    mock_repo.get_list.return_value = programs
    service = ProgramService(mock_repo)

    result = await service.get_list()

    assert result == programs
    mock_repo.get_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_successfull_add_program(mock_repo: Mock) -> None:
    program = Program(
        program_id=1,
        transfer_type="Автобус",
        cost=200,
        transfer_duration_minutes=150,
        start_venue=None,
        end_venue=None,
    )
    mock_repo.add.return_value = program
    service = ProgramService(mock_repo)

    result = await service.add(program)

    assert result == program
    mock_repo.add.assert_awaited_once_with(program)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_add_duplicate_program(
    mock_repo: Mock,
) -> None:
    program = Program(
        program_id=1,
        transfer_type="Автобус",
        cost=200,
        transfer_duration_minutes=150,
        start_venue=None,
        end_venue=None,
    )
    mock_repo.add.side_effect = Exception("Duplicate")
    service = ProgramService(mock_repo)

    with pytest.raises(
        ValueError, match=re.escape("Программа c таким ID уже существует.")
    ):
        await service.add(program)


@pytest.mark.asyncio
async def test_should_successfull_update_existed_program_by_id(mock_repo: Mock) -> None:
    program = Program(
        program_id=1,
        transfer_type="Самолет",
        cost=25866,
        transfer_duration_minutes=300000,
        start_venue=None,
        end_venue=None,
    )
    service = ProgramService(mock_repo)

    result = await service.update(program)

    assert result == program
    mock_repo.update.assert_awaited_once_with(program)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_update_not_existed_program(
    mock_repo: Mock,
) -> None:
    program = Program(
        program_id=1,
        transfer_type="Самолет",
        cost=25866,
        transfer_duration_minutes=300000,
        start_venue=None,
        end_venue=None,
    )
    mock_repo.update.side_effect = Exception("Not found")
    service = ProgramService(mock_repo)

    with pytest.raises(ValueError, match=re.escape("Программа не найдена.")):
        await service.update(program)


@pytest.mark.asyncio
async def test_should_successfull_delete_existed_program(mock_repo: Mock) -> None:
    service = ProgramService(mock_repo)

    await service.delete(123)

    mock_repo.delete.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_delete_not_existed_program(
    mock_repo: Mock,
) -> None:
    mock_repo.delete.side_effect = Exception("Not found")
    service = ProgramService(mock_repo)

    with pytest.raises(
        ValueError, match=re.escape("Программу не получилось удалить.")
    ):
        await service.delete(123)


@pytest.mark.asyncio
async def test_should_successfull_change_transfer_type(mock_repo: Mock) -> None:
    program = Program(
        program_id=1,
        transfer_type="Автобус",
        cost=100,
        transfer_duration_minutes=200,
        start_venue=None,
        end_venue=None,
    )
    mock_repo.change_transfer_type.return_value = program
    service = ProgramService(mock_repo)

    result = await service.change_transfer_type(1, "Автобус")

    assert result == program
    mock_repo.change_transfer_type.assert_awaited_once_with(1, "Автобус")


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_change_transfer_type(
    mock_repo: Mock,
) -> None:
    mock_repo.change_transfer_type.side_effect = Exception("Error")
    service = ProgramService(mock_repo)

    with pytest.raises(
        ValueError, match=re.escape("Не получилось изменить транспорт.")
    ):
        await service.change_transfer_type(1, "Поезд")


@pytest.mark.asyncio
async def test_should_successfull_get_by_venues(mock_repo: Mock) -> None:
    program = Program(
        program_id=1,
        transfer_type="Самолет",
        cost=300,
        transfer_duration_minutes=500,
        start_venue=None,
        end_venue=None,
    )
    mock_repo.get_by_venues.return_value = program
    service = ProgramService(mock_repo)

    result = await service.get_by_venues(1, 2, "Самолет")

    assert result == program
    mock_repo.get_by_venues.assert_awaited_once_with(1, 2, "Самолет")


@pytest.mark.asyncio
async def test_service_should_throw_exception_at_get_by_venues(mock_repo: Mock) -> None:
    mock_repo.get_by_venues.side_effect = Exception("Error")
    service = ProgramService(mock_repo)

    with pytest.raises(
        ValueError, match=re.escape("Программу не получилось найти.")
    ):
        await service.get_by_venues(1, 2, "Самолет")


@pytest.mark.asyncio
async def test_should_failed_get_list(mock_repo: Mock) -> None:
    mock_repo.get_list.return_value = []
    service = ProgramService(mock_repo)

    result = await service.get_list()

    assert result == []
    mock_repo.get_list.assert_awaited_once()

