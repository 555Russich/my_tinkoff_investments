import asyncio
from datetime import datetime, timedelta

from config import FILEPATH_LOGGER
from src.my_logging import get_logger, TZ
from src.api_calls import (
    get_dividends,
    get_shares
)
from src.converter import Converter


FIGI = 'BBG004730N88'


async def main():

    exit()


if __name__ == '__main__':
    get_logger(FILEPATH_LOGGER)
    asyncio.run(main())
