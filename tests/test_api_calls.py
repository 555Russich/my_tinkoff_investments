from tinkoff.invest import (
    Instrument,
    InstrumentIdType,
)

from my_tinkoff.api_calls.instruments import (
    get_shares,
    get_dividends,
    get_instrument_by,
    get_trading_schedules,
)
from my_tinkoff.schemas import Shares
from my_tinkoff.enums import Board
from my_tinkoff.date_utils import DateTimeFactory


async def test_get_shares():
    shares = await get_shares()
    assert isinstance(shares, Shares)


async def test_get_instrument_by_ticker() -> None:
    instrument = await get_instrument_by(
        id='SBER',
        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
        class_code=Board.TQBR
    )
    assert isinstance(instrument, Instrument)


async def test_get_dividends() -> None:
    instrument = await get_instrument_by(
        id='SBER',
        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
        class_code=Board.TQBR
    )

    dividends = await get_dividends(
        instrument=instrument,
        from_=instrument.first_1day_candle_date,
        to=DateTimeFactory.now()
    )
    assert isinstance(dividends, list)


async def test_get_trading_schedules() -> None:
    from datetime import timedelta
    now = DateTimeFactory.now()

    r = await get_trading_schedules(from_=now, to=now + timedelta(days=7))
    print(r)