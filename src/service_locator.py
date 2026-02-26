from __future__ import annotations

import logging

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from abstract_repository.iactivity_repository import IActivityRepository
from abstract_repository.ievent_repository import IEventRepository
from abstract_repository.ilodging_repository import ILodgingRepository
from abstract_repository.iprogram_repository import IProgramRepository
from abstract_repository.isession_repository import ISessionRepository
from abstract_repository.iuser_repository import IUserRepository
from abstract_repository.ivenue_repository import IVenueRepository
from controllers.activity_controller import ActivityController
from controllers.event_controller import EventController
from controllers.lodging_controller import LodgingController
from controllers.program_controller import ProgramController
from controllers.session_controller import SessionController
from controllers.user_controller import UserController
from controllers.venue_controller import VenueController
from repository.activity_repository import ActivityRepository
from repository.event_repository import EventRepository
from repository.lodging_repository import LodgingRepository
from repository.program_repository import ProgramRepository
from repository.session_repository import SessionRepository
from repository.user_repository import UserRepository
from repository.venue_repository import VenueRepository
from services.activity_service import ActivityService
from services.event_service import EventService
from services.lodging_service import LodgingService
from services.program_service import ProgramService
from services.session_service import SessionService
from services.user_service import AuthService
from services.user_service import UserService
from services.venue_service import VenueService
from settings import settings


logger = logging.getLogger(__name__)

_pg_engine: AsyncEngine | None = None
_pg_session_factory: async_sessionmaker[AsyncSession] | None = None


@dataclass
class Repositories:
    def __init__(
        self,
        lodging_repo: ILodgingRepository,
        venue_repo: IVenueRepository,
        program_repo: IProgramRepository,
        activity_repo: IActivityRepository,
        session_repo: ISessionRepository,
        event_repo: IEventRepository,
        user_repo: IUserRepository,
    ):
        self.lodging_repo = lodging_repo
        self.venue_repo = venue_repo
        self.program_repo = program_repo
        self.activity_repo = activity_repo
        self.session_repo = session_repo
        self.event_repo = event_repo
        self.user_repo = user_repo


@dataclass
class Services:
    def __init__(
        self,
        lodging_serv: LodgingService,
        venue_serv: VenueService,
        program_serv: ProgramService,
        activity_serv: ActivityService,
        session_serv: SessionService,
        event_serv: EventService,
        user_serv: UserService,
        auth_serv: AuthService,
    ):
        self.lodging_serv = lodging_serv
        self.venue_serv = venue_serv
        self.program_serv = program_serv
        self.activity_serv = activity_serv
        self.session_serv = session_serv
        self.event_serv = event_serv
        self.user_serv = user_serv
        self.auth_serv = auth_serv


@dataclass
class Controllers:
    def __init__(
        self,
        lodging_contr: LodgingController,
        session_contr: SessionController,
        activity_contr: ActivityController,
        event_contr: EventController,
        user_contr: UserController,
        program_contr: ProgramController,
        venue_contr: VenueController,
    ):
        self.lodging_contr = lodging_contr
        self.venue_contr = venue_contr
        self.session_contr = session_contr
        self.program_contr = program_contr
        self.activity_contr = activity_contr
        self.event_contr = event_contr
        self.user_contr = user_contr


class ServiceLocator:
    def __init__(
        self, repositories: Repositories, services: Services, controllers: Controllers
    ):
        self.repositories = repositories
        self.services = services
        self.controllers = controllers

    def get_lodging_repo(self) -> ILodgingRepository:
        return self.repositories.lodging_repo

    def get_venue_repo(self) -> IVenueRepository:
        return self.repositories.venue_repo

    def get_program_repo(self) -> IProgramRepository:
        return self.repositories.program_repo

    def get_activity_repo(self) -> IActivityRepository:
        return self.repositories.activity_repo

    def get_session_repo(self) -> ISessionRepository:
        return self.repositories.session_repo

    def get_event_repo(self) -> IEventRepository:
        return self.repositories.event_repo

    def get_user_repo(self) -> IUserRepository:
        return self.repositories.user_repo

    def get_lodging_serv(self) -> LodgingService:
        return self.services.lodging_serv

    def get_venue_serv(self) -> VenueService:
        return self.services.venue_serv

    def get_program_serv(self) -> ProgramService:
        return self.services.program_serv

    def get_activity_serv(self) -> ActivityService:
        return self.services.activity_serv

    def get_session_serv(self) -> SessionService:
        return self.services.session_serv

    def get_event_serv(self) -> EventService:
        return self.services.event_serv

    def get_user_serv(self) -> UserService:
        return self.services.user_serv

    def get_auth_serv(self) -> AuthService:
        return self.services.auth_serv

    def get_lodging_contr(self) -> LodgingController:
        return self.controllers.lodging_contr

    def get_venue_contr(self) -> VenueController:
        return self.controllers.venue_contr

    def get_session_contr(self) -> SessionController:
        return self.controllers.session_contr

    def get_program_contr(self) -> ProgramController:
        return self.controllers.program_contr

    def get_activity_contr(self) -> ActivityController:
        return self.controllers.activity_contr

    def get_event_contr(self) -> EventController:
        return self.controllers.event_contr

    def get_user_contr(self) -> UserController:
        return self.controllers.user_contr


async def get_service_locator() -> ServiceLocator:
    global _pg_engine, _pg_session_factory

    if _pg_engine is None:
        _pg_engine = create_async_engine(
            settings.DATABASE_URL_ASYNC,
            connect_args={"server_settings": {"search_path": "event_db"}},
        )
        _pg_session_factory = async_sessionmaker(_pg_engine, expire_on_commit=False)

    assert _pg_session_factory is not None
    session: AsyncSession = _pg_session_factory()

    venue_repo: IVenueRepository = VenueRepository(session)
    program_repo: IProgramRepository = ProgramRepository(session, venue_repo)
    lodging_repo: ILodgingRepository = LodgingRepository(session, venue_repo)
    activity_repo: IActivityRepository = ActivityRepository(session, venue_repo)
    user_repo: IUserRepository = UserRepository(session)
    event_repo: IEventRepository = EventRepository(
        session, user_repo, activity_repo, lodging_repo
    )
    session_repo: ISessionRepository = SessionRepository(
        session, program_repo, event_repo
    )

    lodging_serv = LodgingService(lodging_repo)
    venue_serv = VenueService(venue_repo)
    program_serv = ProgramService(program_repo)
    activity_serv = ActivityService(activity_repo)
    session_serv = SessionService(session_repo)
    event_serv = EventService(event_repo)
    user_serv = UserService(user_repo)
    auth_serv = AuthService(user_repo)

    repositories = Repositories(
        lodging_repo,
        venue_repo,
        program_repo,
        activity_repo,
        session_repo,
        event_repo,
        user_repo,
    )

    venue_contr = VenueController(venue_serv)
    session_contr = SessionController(
        session_serv, event_serv, program_serv, user_serv, activity_serv, lodging_serv
    )
    program_contr = ProgramController(program_serv, venue_serv)
    lodging_contr = LodgingController(lodging_serv, venue_serv)
    activity_contr = ActivityController(activity_serv, venue_serv)
    event_contr = EventController(event_serv, user_serv, activity_serv, lodging_serv)
    user_contr = UserController(user_serv, auth_serv)

    services = Services(
        lodging_serv,
        venue_serv,
        program_serv,
        activity_serv,
        session_serv,
        event_serv,
        user_serv,
        auth_serv,
    )
    controllers = Controllers(
        lodging_contr,
        session_contr,
        activity_contr,
        event_contr,
        user_contr,
        program_contr,
        venue_contr,
    )

    return ServiceLocator(repositories, services, controllers)
