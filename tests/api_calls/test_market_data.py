import pytest

from tinkoff.invest import GetTradingStatusResponse

from my_tinkoff import (
    get_candles,
    get_trading_status
)
from my_tinkoff.schemas import Candles, Candle
from tests.dataset import SBER, dataset_candles


@pytest.mark.parametrize("instrument,case", dataset_candles)
async def test_get_candles(instrument, case) -> None:
    r = await get_candles(instrument_id=instrument.uid, from_=case.dt_from, to=case.dt_to, interval=case.interval)
    assert isinstance(r, Candles)
    assert isinstance(r[0], Candle)
    assert len(r) == case.count_candles
    assert r[0].time == case.dt_first_candle
    assert r[-1].time == case.dt_last_candle


async def test_get_trading_status() -> None:
    r = await get_trading_status(instrument_id=SBER.uid)
    assert isinstance(r, GetTradingStatusResponse)
