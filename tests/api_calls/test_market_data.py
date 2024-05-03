import pytest

from tinkoff.invest import GetTradingStatusResponse

from src.my_tinkoff.api_calls.market_data import (
    get_candles,
    get_trading_status
)
from src.my_tinkoff.schemas import Candles, Candle
from tests.dataset import SBER, dataset_candles


@pytest.mark.parametrize("instrument,case", dataset_candles)
async def test_get_candles(instrument, case) -> None:
    # from datetime import datetime, timezone
    # from tinkoff.invest import CandleInterval
    # from_ = datetime(year=2023, month=10, day=25, hour=20, minute=30, tzinfo=timezone.utc)
    # to = datetime(year=2023, month=10, day=26, hour=7, minute=30, tzinfo=timezone.utc)
    # r = await get_candles(instrument_id='974077c4-d893-4058-9314-8f1b64a444b8', from_=from_, to=to, interval=CandleInterval.CANDLE_INTERVAL_1_MIN)
    # for c in r:
    #     print(c)
    # exit()

    r = await get_candles(instrument_id=instrument.uid, from_=case.dt_from, to=case.dt_to, interval=case.interval)
    assert isinstance(r, Candles)
    assert isinstance(r[0], Candle)
    # print(len(r))
    # print(f'{r[0].time=}')
    # print(f'{r[-1].time=}')
    assert len(r) == case.count_candles
    assert r[0].time == case.dt_first_candle
    assert r[-1].time == case.dt_last_candle


async def test_get_trading_status() -> None:
    r = await get_trading_status(instrument_id=SBER.uid)
    assert isinstance(r, GetTradingStatusResponse)
