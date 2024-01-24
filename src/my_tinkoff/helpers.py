import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
    CandleInterval,
    Instrument,
    TradeDirection,
)

from my_tinkoff.api_calls.market_data import get_candles
from my_tinkoff.date_utils import DateTimeFactory, dt_form_sys
from my_tinkoff.exceptions import (
    UnexpectedCandleInterval,
    RequestedCandleOutOfRange
)


async def configure_datetime_range(
        instrument: Instrument,
        from_: datetime,
        to: datetime,
        interval: CandleInterval
) -> tuple[datetime, datetime]:
    is_from_defined, is_to_defined = False, False
    delta = timedelta(days=15)

    if interval == CandleInterval.CANDLE_INTERVAL_1_MIN:
        from_ = from_
    elif interval == CandleInterval.CANDLE_INTERVAL_DAY:
        from_ = from_.replace(hour=0, minute=0, second=0, microsecond=0)
        logging.debug(f'ticker={instrument.ticker} | 1day candle={instrument.first_1day_candle_date}')

    try:
        check_first_candle_availability(instrument, dt=from_, interval=interval)
    except RequestedCandleOutOfRange as ex:
        logging.warning(f'ticker={instrument.ticker} from_={dt_form_sys.datetime_strf(from_)} < first_candle='
                        f'{dt_form_sys.datetime_strf(ex.dt_first_available_candle)}')
        from_ = ex.dt_first_available_candle
        is_from_defined = True

    if to > DateTimeFactory.now():
        logging.warning(f'to can\'t be later than datetime now...')
        to = DateTimeFactory.now()
        is_to_defined = True

    # check if from_ was trading day OR find the closest early day before
    from_temp = from_ - delta
    to_temp = from_ + delta
    closest_day_early = None

    while not is_from_defined:
        candles = await get_candles(
            figi=instrument.figi,
            from_=from_temp, to=to_temp,
            delta=delta * 2,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        )

        for candle in candles:
            match candle.time.replace(hour=0):
                case x if x == from_:
                    from_ = candle.time
                    is_from_defined = True
                    break
                case x if x < from_:
                    closest_day_early = x
        else:
            if closest_day_early:
                from_ = closest_day_early
                is_from_defined = True

            from_temp -= delta * 2
            to_temp -= delta * 2

    # check if "to" is trading day OR find the closest later day after OR
    # if to is today and last trading day was yesterday, the closest earlier day
    to_date = to.replace(hour=0, minute=0, second=0, microsecond=0)
    from_temp = to - delta
    to_temp = to + delta
    closest_day_later = None
    closest_day_early = None

    while not is_to_defined:
        candles = await get_candles(
            figi=instrument.figi,
            from_=from_temp, to=to_temp,
            delta=delta * 2,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        )

        if not candles or not candles[-1].is_complete:
            break

        for candle in candles:
            match candle.time.replace(hour=0):
                case x if x == to_date:
                    is_to_defined = True
                    break
                case x if x > to_date and not closest_day_later:
                    closest_day_later = x
                case x if x < to_date:
                    closest_day_early = x
        else:
            if closest_day_later:
                to = closest_day_later
                is_to_defined = True
            elif closest_day_early:
                to = closest_day_early.replace(hour=23, minute=59, second=59, microsecond=999999)
                is_to_defined = True

            from_temp += delta * 2
            to_temp += delta * 2

    return from_, to


def get_opposite_direction(direction: TradeDirection) -> TradeDirection:
    if direction == TradeDirection.TRADE_DIRECTION_SELL:
        return TradeDirection.TRADE_DIRECTION_BUY
    elif direction == TradeDirection.TRADE_DIRECTION_BUY:
        return TradeDirection.TRADE_DIRECTION_SELL


def check_first_candle_availability(instrument: Instrument, dt: datetime, interval: CandleInterval) -> None:
    if interval == CandleInterval.CANDLE_INTERVAL_1_MIN:
        if dt < instrument.first_1min_candle_date:
            raise RequestedCandleOutOfRange(dt_first_available_candle=instrument.first_1min_candle_date)
    elif interval == CandleInterval.CANDLE_INTERVAL_DAY:
        if DateTimeFactory.replace_time(dt) < DateTimeFactory.replace_time(instrument.first_1day_candle_date):
            raise RequestedCandleOutOfRange(dt_first_available_candle=instrument.first_1day_candle_date)
    else:
        raise UnexpectedCandleInterval(repr(interval))
