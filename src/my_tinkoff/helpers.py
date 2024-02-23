import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
    CandleInterval,
    Instrument,
    TradeDirection,
    Quotation,
    HistoricCandle,
    MoneyValue,
)

from my_tinkoff.date_utils import DateTimeFactory, dt_form_sys
from my_tinkoff.schemas import Candle
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
    from my_tinkoff.api_calls.market_data import get_candles

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

    # check if from_ was trading day OR find the closest early day before
    from_temp = from_ - delta
    to_temp = from_ + delta
    closest_day_early = None

    while not is_from_defined:
        candles = await get_candles(
            instrument_id=instrument.uid,
            from_=from_temp, to=to_temp,
            delta=delta * 2,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        )

        if not candles:
            # Share IPO was after `to_temp`, that's why list of candles is empty
            break

        for candle in candles:
            if candle.time.date() == from_.date():
                is_from_defined = True
                break
            if candle.time.date() < from_.date():
                closest_day_early = candle.time
        else:
            if closest_day_early:
                from_ = closest_day_early.replace(hour=from_.hour, minute=from_.minute,
                                                  second=from_.second, microsecond=from_.microsecond)
                is_from_defined = True

            from_temp -= delta * 2
            to_temp -= delta * 2

    # check if "to" is trading day OR find the closest later day after OR
    # if to is today and last trading day was yesterday, the closest earlier day
    from_temp = to - delta
    to_temp = to + delta
    closest_day_later = None
    closest_day_early = None

    while not is_to_defined:
        candles = await get_candles(
            instrument_id=instrument.uid,
            from_=from_temp, to=to_temp,
            delta=delta * 2,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        )

        if not candles or not candles[-1].is_complete:
            break

        for candle in candles:
            if candle.time.date() == to.date():
                is_to_defined = True
                break
            elif candle.time.date() > to.date() and not closest_day_later:
                closest_day_later = candle.time
            elif candle.time.date() < to.date():
                closest_day_early = candle.time
        else:
            if closest_day_later:
                to = closest_day_later.replace(hour=to.hour, minute=to.minute,
                                               second=to.second, microsecond=to.microsecond)
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


def configure_datetime_from(from_: datetime, instrument: Instrument, interval: CandleInterval) -> datetime:
    try:
        check_first_candle_availability(instrument=instrument, dt=from_, interval=interval)
        from_configured = from_
    except RequestedCandleOutOfRange as ex:
        logging.warning(f'ticker={instrument.ticker} from_={dt_form_sys.datetime_strf(from_)} < first_candle='
                        f'{dt_form_sys.datetime_strf(ex.dt_first_available_candle)}')
        from_configured = ex.dt_first_available_candle
    return from_configured


def check_first_candle_availability(instrument: Instrument, dt: datetime, interval: CandleInterval) -> None:
    if interval == CandleInterval.CANDLE_INTERVAL_1_MIN:
        if dt < instrument.first_1min_candle_date:
            raise RequestedCandleOutOfRange(dt_first_available_candle=instrument.first_1min_candle_date)
    elif interval == CandleInterval.CANDLE_INTERVAL_DAY:
        if DateTimeFactory.replace_time(dt) < DateTimeFactory.replace_time(instrument.first_1day_candle_date):
            raise RequestedCandleOutOfRange(dt_first_available_candle=instrument.first_1day_candle_date)
    else:
        raise UnexpectedCandleInterval(repr(interval))


def quotation2decimal(value: Quotation) -> float:
    return value.units + value.nano * 10 ** -9


def decimal2quotation(value: float) -> Quotation:
    units, nano = [x for x in str(value).split('.')]
    return Quotation(int(units), int(nano * 10 ** 9))


def moneyvalue2quotation(v: MoneyValue) -> Quotation:
    return Quotation(units=v.units, nano=v.nano)


def convert_candle(candle: HistoricCandle) -> Candle:
    return Candle(
        quotation2decimal(candle.open),
        quotation2decimal(candle.high),
        quotation2decimal(candle.low),
        quotation2decimal(candle.close),
        candle.volume,
        candle.time,
        candle.is_complete
    )


def get_delta_by_interval(interval: CandleInterval) -> timedelta:
    match interval:
        case CandleInterval.CANDLE_INTERVAL_DAY:
            return timedelta(days=365)
        case CandleInterval.CANDLE_INTERVAL_1_MIN:
            return timedelta(days=1)
        case _:
            raise UnexpectedCandleInterval(interval)
