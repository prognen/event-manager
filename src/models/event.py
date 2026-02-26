from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from models.activity import Activity
from models.lodging import Lodging
from models.user import User


class Event(BaseModel):
    event_id: int
    status: str
    users: list[User] = Field(default_factory=list, description="Список участников")
    activities: list[Activity] = Field(
        default_factory=list, description="Список активностей"
    )
    lodgings: list[Lodging] = Field(
        default_factory=list, description="Список размещений"
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("event_id")
    @classmethod
    def check_event_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("event_id должен быть положительным числом")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_types = {"Активное", "Завершено", "Отменено"}
        if v not in allowed_types:
            raise ValueError(
                f'status должен быть одним из следующих: {", ".join(allowed_types)}'
            )
        return v

    @field_validator("users")
    @classmethod
    def check_users(cls, value: list[User]) -> list[User]:
        if value is not None:
            if not isinstance(value, list):
                raise ValueError("users должен быть списком")
            if not value:
                raise ValueError("Список users не должен быть пустым")
            if not all(isinstance(item, User) for item in value):
                raise ValueError("Bce элементы users должны быть экземплярами User")
        return value

    @field_validator("activities")
    @classmethod
    def check_activities(cls, value: list[Activity]) -> list[Activity]:
        if value is not None:
            if not isinstance(value, list):
                raise ValueError("activities должен быть списком")
            if not value:
                raise ValueError("Список activities не должен быть пустым")
            if not all(isinstance(item, Activity) for item in value):
                raise ValueError(
                    "Bce элементы activities должны быть экземплярами Activity"
                )
        return value

    @field_validator("lodgings")
    @classmethod
    def check_lodgings(cls, value: list[Lodging]) -> list[Lodging]:
        if value is not None:
            if not isinstance(value, list):
                raise ValueError("lodgings должен быть списком")
            if not value:
                raise ValueError("Список lodgings не должен быть пустым")
            if not all(isinstance(item, Lodging) for item in value):
                raise ValueError(
                    "Bce элементы lodgings должны быть экземплярами Lodging"
                )
        return value
