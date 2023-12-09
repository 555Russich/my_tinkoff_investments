import logging
from datetime import datetime, timedelta

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest import CandleInterval
from tinkoff.invest.exceptions import AioRequestError
from grpc import StatusCode

from src.my_logging import log_and_exit
from src.token_manager import token_controller
from src.converter import Converter
from src.exceptions import ResourceExhausted
from src.schemas import Candles


@token_controller()
async def get_candles(
        figi: str,
        from_: datetime,
        to: datetime,
        interval: CandleInterval = CandleInterval.CANDLE_INTERVAL_1_MIN,
        delta: timedelta = timedelta(days=1),
        client: AsyncServices = None
) -> Candles:
    candles = Candles()
    while True:
        to_temp = from_ + delta
        if to_temp > to:
            to_temp = to

        logging.info(f'{len(candles)=} | {from_} | {to_temp} | {to}')

        try:
            r = await client.market_data.get_candles(
                figi=figi, interval=interval,
                from_=from_, to=to_temp
            )
            candles += [Converter.candle(candle) for candle in r.candles]
        except AioRequestError as ex:
            if ex.code == StatusCode.RESOURCE_EXHAUSTED:
                raise ResourceExhausted(candles)
            elif ex.code == StatusCode.UNAVAILABLE:
                logging.warning(ex, exc_info=True)
                continue
            else:
                log_and_exit(ex)
        except Exception as ex:
            log_and_exit(ex)

        from_ = to_temp
        if from_ >= to:
            return candles
