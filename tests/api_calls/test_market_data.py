from datetime import datetime, timedelta

from tinkoff.invest import (
    CandleInterval,
    GetTradingStatusResponse
)
from my_tinkoff.api_calls.market_data import (
    get_candles,
    get_trading_status
)
from my_tinkoff.date_utils import TZ_UTC
from my_tinkoff.schemas import Candles, Candle

from tests.dataset import Dataset


async def test_get_candles() -> None:
    to = datetime(year=2024, month=2, day=22, hour=13, minute=0, tzinfo=TZ_UTC)
    from_ = to - timedelta(days=3)

    r = await get_candles(
        instrument_id=Dataset.INSTRUMENT_ID,
        from_=from_,
        to=to,
        interval=CandleInterval.CANDLE_INTERVAL_1_MIN
    )
    assert isinstance(r, Candles)
    assert isinstance(r[0], Candle)
    assert len(r) == 2435


async def test_get_trading_status() -> None:
    r = await get_trading_status(instrument_id=Dataset.INSTRUMENT_ID)
    assert isinstance(r, GetTradingStatusResponse)
