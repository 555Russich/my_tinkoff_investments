from tinkoff.invest import InstrumentIdType

from config import FILEPATH_LOGGER
from my_tinkoff_investments.my_logging import get_logger
from my_tinkoff_investments.api_calls.instruments import get_instrument_by


async def main():
    instrument = await get_instrument_by(id='AGRO', id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code='TQBR')
    print(instrument)
    # CSVCandles.download_or_read(instrument=)

if __name__ == "__main__":
    import asyncio
    get_logger(FILEPATH_LOGGER)
    asyncio.run(main())
