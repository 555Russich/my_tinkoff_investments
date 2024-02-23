import pytest
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

from tests.dataset import test_instruments, SBER


async def test_get_shares():
    shares = await get_shares()
    assert isinstance(shares, Shares)


@pytest.mark.parametrize('instrument_data', test_instruments)
async def test_get_instrument_by_ticker(instrument_data) -> None:
    instrument = await get_instrument_by(
        id=instrument_data.ticker,
        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
        class_code=instrument_data.class_code
    )
    # print(instrument)
    # print(instrument.first_1min_candle_date)
    assert isinstance(instrument, Instrument)
    assert instrument.ticker == instrument_data.ticker
    assert instrument.class_code == instrument_data.class_code


async def test_get_dividends() -> None:
    instrument = await get_instrument_by(
        id=SBER.ticker,
        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
        class_code=SBER.class_code
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
