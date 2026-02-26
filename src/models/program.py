from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from models.venue import Venue


class Program(BaseModel):
    program_id: int
    type_transport: str
    cost: int
    distance: int
    from_venue: Venue | None = Field(
        default=None, description="Площадка отправления"
    )
    to_venue: Venue | None = Field(
        default=None, description="Площадка назначения"
    )
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("program_id")
    @classmethod
    def check_program_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("program_id должен быть положительным числом")
        return value

    @field_validator("cost")
    @classmethod
    def check_cost_is_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("cost должен быть положительным числом")
        return value

    @field_validator("type_transport")
    @classmethod
    def validate_type_transport(cls, v: str) -> str:
        allowed_types = {"Автобус", "Самолет", "Автомобиль", "Паром", "Поезд"}
        if v not in allowed_types:
            raise ValueError(
                f'type_transport должен быть одним из следующих: {", ".join(allowed_types)}'
            )
        return v

    @field_validator("distance")
    @classmethod
    def check_distance_is_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("distance должен быть положительным числом")
        return value

    @field_validator("from_venue")
    @classmethod
    def check_from_venue(cls, value: Venue | None) -> Venue | None:
        if value is not None and not isinstance(value, Venue):
            raise ValueError("from_venue должен быть экземпляром Venue")
        return value

    @field_validator("to_venue")
    @classmethod
    def check_to_venue(cls, value: Venue | None) -> Venue | None:
        if value is not None and not isinstance(value, Venue):
            raise ValueError("to_venue должен быть экземпляром Venue")
        return value
