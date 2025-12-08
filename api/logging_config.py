# api/logging_config.py
from __future__ import annotations

from logging.config import dictConfig


def configure_logging() -> None:
    """
    קונפיגורציית לוגים בסיסית:
    - פורמט אחיד time/level/logger/message
    - קל להחליף ל-JSON בעתיד אם נרצה חיבור ל-ELK / Datadog
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
        },
        "loggers": {
            "uvicorn.error": {"handlers": ["console"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["console"], "level": "INFO"},
            "demobot": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }

    dictConfig(logging_config)
