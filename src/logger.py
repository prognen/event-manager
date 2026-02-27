from __future__ import annotations

import configparser
import logging
import logging.handlers
import os
import sys

from pathlib import Path


def setup_logging() -> None:
    config = configparser.ConfigParser()
    config.read("config.cfg")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    try:
        # LOG_LEVEL из env (для бенчмарка/Лаба 5) имеет приоритет над config.cfg
        log_level_str = os.environ.get("LOG_LEVEL") or config["app"].get("LOG_LEVEL", "DEBUG")
        log_level = getattr(logging, log_level_str.upper(), logging.DEBUG)

        simple_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        detailed_format = "%(asctime)s - %(name)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s"

        # Базовый логгер
        logger = logging.getLogger()
        logger.setLevel(log_level)

        # Обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(simple_format))

        debug_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "debug.log", maxBytes=10 * 1024 * 1024, backupCount=5
        )
        debug_handler.setLevel(log_level)
        debug_handler.setFormatter(logging.Formatter(detailed_format))

        # Обработчик для ошибок
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "error.log", maxBytes=10 * 1024 * 1024, backupCount=5
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(logging.Formatter(detailed_format))

        # Добавляем обработчики
        logger.addHandler(console_handler)
        logger.addHandler(debug_handler)
        logger.addHandler(error_handler)

        # Настраиваем логирование для сторонних библиотек
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("uvicorn").setLevel(logging.INFO)
    except Exception as e:
        print(f"Ошибка при инициализации логгера: {e}")
        sys.exit(1)
