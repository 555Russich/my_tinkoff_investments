from datetime import timedelta

from tinkoff.invest import (
    Instrument,
    InstrumentIdType,
    TradingSchedule
)

from my_tinkoff.api_calls.instruments import (
    get_shares,
    get_dividends,
    get_instrument_by,
    get_trading_schedules,
)
from my_tinkoff.schemas import Shares
from my_tinkoff.date_utils import DateTimeFactory

from tests.dataset import Dataset


async def test_get_shares():
    shares = await get_shares()
    assert isinstance(shares, Shares)


async def test_get_instrument_by_ticker() -> None:
    instrument = await get_instrument_by(
        id=Dataset.TICKER,
        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
        class_code=Dataset.CLASS_CODE
    )
    print(instrument)
    print(instrument.first_1min_candle_date)
    assert isinstance(instrument, Instrument)
    assert instrument.ticker == Dataset.TICKER
    assert instrument.class_code == Dataset.CLASS_CODE


async def test_get_dividends() -> None:
    instrument = await get_instrument_by(
        id=Dataset.TICKER,
        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
        class_code=Dataset.CLASS_CODE
    )

    dividends = await get_dividends(
        instrument=instrument,
        from_=instrument.first_1day_candle_date,
        to=DateTimeFactory.now()
    )
    assert isinstance(dividends, list)


async def test_get_trading_schedules() -> None:
    now = DateTimeFactory.now()
    r = await get_trading_schedules(from_=now, to=now + timedelta(days=2))
    assert isinstance(r, list)
    assert isinstance(r[0], TradingSchedule)
