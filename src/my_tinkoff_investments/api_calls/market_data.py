import logging
from datetime import datetime, timedelta

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest import CandleInterval
from tinkoff.invest.exceptions import AioRequestError
from grpc import StatusCode

from my_tinkoff_investments.token_manager import token_controller
from my_tinkoff_investments.converter import convert_candle
from my_tinkoff_investments.exceptions import ResourceExhausted, UnexpectedCandleInterval
from my_tinkoff_investments.schemas import Candles


@token_controller()
async def get_candles(
        figi: str,
        from_: datetime,
        to: datetime,
        interval: CandleInterval,
        delta: timedelta = None,
        client: AsyncServices = None
) -> Candles:
    if delta is None:
        delta = _get_delta_by_interval(interval)

    candles = Candles()
    while True:
        to_temp = from_ + delta
        if to_temp > to:
            to_temp = to

        logging.debug(f'{len(candles)=} | {from_} | {to_temp} | {to}')

        try:
            r = await client.market_data.get_candles(
                figi=figi, interval=interval,
                from_=from_, to=to_temp
            )
            candles += [convert_candle(candle) for candle in r.candles if candle.time <= to_temp]
        except AioRequestError as ex:
            if ex.code == StatusCode.RESOURCE_EXHAUSTED:
                raise ResourceExhausted(candles)
            elif ex.code == StatusCode.UNAVAILABLE:
                logging.warning(ex, exc_info=True)
                continue
            else:
                raise ex
        except Exception as ex:
            raise ex

        from_ = to_temp
        if from_ >= to:
            return candles


def _get_delta_by_interval(interval: CandleInterval) -> timedelta:
    match interval:
        case CandleInterval.CANDLE_INTERVAL_DAY:
            return timedelta(days=365)
        case CandleInterval.CANDLE_INTERVAL_1_MIN:
            return timedelta(days=1)
        case _:
            raise UnexpectedCandleInterval(interval)
