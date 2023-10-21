import logging
import sys
from pathlib import Path
from datetime import datetime

from config import TZ


def get_logger(filepath: Path) -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        encoding='utf-8',
        format="[{asctime},{msecs:03.0f}]:[{levelname}]:{message}",
        datefmt='%d.%m.%Y %H:%M:%S',
        style='{',
        handlers=[
            logging.FileHandler(filepath, mode='a'),
            logging.StreamHandler(sys.stdout),
        ]
    )

    logging.Formatter.converter = lambda *args: datetime.now(tz=TZ).timetuple()
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def log_and_exit(ex: Exception) -> None:
    logging.error(ex, exc_info=True)
    exit(1)
