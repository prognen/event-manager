from __future__ import annotations

import configparser
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, "config.cfg"))


class Settings:
    def __init__(self) -> None:
        app = config["app"]
        # DATABASE_URL из env (Docker) имеет приоритет
        db_url = os.environ.get("DATABASE_URL") or app["DATABASE_URL_ASYNC"]
        if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        self.DATABASE_URL_ASYNC: str = db_url
        self.SECRET_KEY: str = app["SECRET_KEY"]
        self.ALGORITHM: str = app.get("ALGORITHM", "HS256")
        self.SESSION_TIMEOUT: int = int(app.get("SESSION_TIMEOUT", 30))

    def get_secret_key(self) -> str:
        return self.SECRET_KEY


settings = Settings()
