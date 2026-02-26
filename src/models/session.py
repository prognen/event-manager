from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import ValidationInfo
from pydantic import field_validator

from models.program import Program
from models.event import Event


class Session(BaseModel):
    session_id: int
    program: Program | None = Field(
        default=None, description="Программа маршрута"
    )
    event: Event | None = Field(default=None, description="Мероприятие")
    start_time: datetime
    end_time: datetime
    type: str

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("session_id")
    @classmethod
    def check_session_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("session_id должен быть положительным числом")
        return value

    @field_validator("program")
    @classmethod
    def check_program(cls, value: Program | None) -> Program | None:
        if value is not None and not isinstance(value, Program):
            raise ValueError("program должен быть экземпляром Program")
        return value

    @field_validator("end_time")
    @classmethod
    def check_datetime_order(cls, value: datetime, values: ValidationInfo) -> datetime:
        entry_time = values.data["start_time"]
        if entry_time and value <= entry_time:
            raise ValueError("end_time должен быть позже start_time")
        return value

    @field_validator("event")
    @classmethod
    def check_event(cls, value: Event | None) -> Event | None:
        if value is not None and not isinstance(value, Event):
            raise ValueError("event должен быть экземпляром Event")
        return value

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed_types = {"Официальные", "Рекомендованные", "Личные"}
        if v not in allowed_types:
            raise ValueError(
                f'type должен быть одним из следующих: {", ".join(allowed_types)}'
            )
        return v
