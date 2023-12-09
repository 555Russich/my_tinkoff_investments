import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
    InstrumentIdType,
    InstrumentType,
    CandleInterval,
)

from config import FILEPATH_LOGGER
from src.date_utils import DateTimeFactory
from src.my_logging import get_logger
from src.csv_candles import CSVCandles
from src.api_calls.instruments import get_instrument_by, get_shares
from src.instruments.shares import Shares


FIGI = 'BBG004730N88'


async def main():
    instrument = await get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=FIGI)
    # await get_all_instrument_history(instrument=instrument, interval=CandleInterval.CANDLE_INTERVAL_DAY)

    # await download_existing_instruments_by_type(
    #     instruments_type=InstrumentType.INSTRUMENT_TYPE_SHARE,
    #     interval=CandleInterval.CANDLE_INTERVAL_DAY
    # )

    # CSVCandles.download_or_read()

    # print((await get_shares())[0])
    # shares = await Shares.from_TQBR()
    # print(shares)

    candles = await CSVCandles.download_or_read(
        instrument=instrument,
        interval=CandleInterval.CANDLE_INTERVAL_DAY,
        from_=DateTimeFactory.now()-timedelta(days=365),
        to=DateTimeFactory.now(),
        delta=timedelta(days=365)
    )
    df = candles.df()
    print(df)
    print(df.close.iloc[-1])




if __name__ == "__main__":
    import asyncio
    get_logger(FILEPATH_LOGGER)
    asyncio.run(main())
