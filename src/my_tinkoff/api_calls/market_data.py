import logging
from datetime import datetime, timedelta

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.exceptions import AioRequestError
from tinkoff.invest import (
    CandleInterval,
    GetTradingStatusResponse,
)
from grpc import StatusCode

from src.my_tinkoff.token_manager import token_controller
from src.my_tinkoff.helpers import convert_candle, get_delta_by_interval
from src.my_tinkoff.exceptions import ResourceExhausted
from src.my_tinkoff.schemas import Candles


@token_controller()
async def get_candles(
        instrument_id: str,
        from_: datetime,
        to: datetime,
        interval: CandleInterval,
        delta: timedelta = None,
        client: AsyncServices = None
) -> Candles:
    if delta is None:
        delta = get_delta_by_interval(interval)

    candles = Candles()
    while True:
        to_temp = from_ + delta
        if to_temp > to:
            to_temp = to

        logging.debug(f'{len(candles)=} | from_={from_} | to_temp={to_temp} | to={to}')

        try:
            r = await client.market_data.get_candles(
                instrument_id=instrument_id, interval=interval,
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


@token_controller(single_response=True)
async def get_trading_status(instrument_id: str, client: AsyncServices = None) -> GetTradingStatusResponse:
    return await client.market_data.get_trading_status(instrument_id=instrument_id)
