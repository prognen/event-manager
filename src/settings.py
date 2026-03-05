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
        self.EXTERNAL_SERVICE_MODE: str = os.environ.get(
            "EXTERNAL_SERVICE_MODE",
            app.get("EXTERNAL_SERVICE_MODE", "real"),
        )
        self.EXTERNAL_SERVICE_REAL_BASE_URL: str = os.environ.get(
            "EXTERNAL_SERVICE_REAL_BASE_URL",
            app.get(
                "EXTERNAL_SERVICE_REAL_BASE_URL",
                "https://jsonplaceholder.typicode.com",
            ),
        )
        self.EXTERNAL_SERVICE_MOCK_BASE_URL: str = os.environ.get(
            "EXTERNAL_SERVICE_MOCK_BASE_URL",
            app.get("EXTERNAL_SERVICE_MOCK_BASE_URL", "http://localhost:8090"),
        )
        self.EXTERNAL_SERVICE_TIMEOUT_SEC: float = float(
            os.environ.get(
                "EXTERNAL_SERVICE_TIMEOUT_SEC",
                app.get("EXTERNAL_SERVICE_TIMEOUT_SEC", "5"),
            )
        )

    def get_secret_key(self) -> str:
        return self.SECRET_KEY


settings = Settings()
