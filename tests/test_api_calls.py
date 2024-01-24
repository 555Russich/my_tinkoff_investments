from tinkoff.invest import (
    Instrument,
    InstrumentIdType,
)

from my_tinkoff.api_calls.instruments import (
    get_shares,
    get_dividends,
    get_instrument_by,
)
from my_tinkoff.schemas import Shares
from my_tinkoff.enums import Board


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
    dividends = await get_dividends()
    print(dividends)