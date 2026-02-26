from __future__ import annotations

import re

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from models.venue import Venue


class Activity(BaseModel):
    activity_id: int
    duration: str
    address: str
    activity_type: str
    activity_time: datetime
    venue: Venue | None = Field(default=None, description="Площадка")
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("activity_id")
    @classmethod
    def check_activity_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("activity_id должен быть положительным числом")
        return value

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        if not re.match(r"^\d+\s*(час|часа|часов)$", v):
            raise ValueError("Продолжительность должна быть в часах")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not v:
            raise ValueError("Address must not be empty")
        return v

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str) -> str:
        allowed_types = {
            "Мастер-класс",
            "Выступление",
            "Выставка",
            "Церемония",
            "Экскурсия",
            "Нетворкинг",
        }
        if v not in allowed_types:
            raise ValueError(
                f'activity_type должен быть одним из следующих: {", ".join(allowed_types)}'
            )
        return v
