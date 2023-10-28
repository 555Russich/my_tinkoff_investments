import logging

from tinkoff.invest import (
    InstrumentIdType,
    InstrumentType,
    CandleInterval,
)

from config import FILEPATH_LOGGER
from src.my_logging import get_logger
from src.api_calls import get_instrument_by
from src.market_data import (
    get_all_instrument_history,
    download_existing_instruments_by_type
)


FIGI = 'BBG004730N88'


async def main():
    # instrument = await get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=FIGI)
    # await get_all_instrument_history(instrument=instrument, interval=CandleInterval.CANDLE_INTERVAL_DAY)

    # await download_existing_instruments_by_type(
    #     instruments_type=InstrumentType.INSTRUMENT_TYPE_SHARE,
    #     interval=CandleInterval.CANDLE_INTERVAL_DAY
    # )

    from src.instruments import Instruments
    await Instruments.get_shares()


if __name__ == "__main__":
    import asyncio
    get_logger(FILEPATH_LOGGER)
    asyncio.run(main())
