import logging
from pathlib import Path
from datetime import datetime, timedelta

from tinkoff.invest import (
    CandleInterval,
    Instrument,
    InstrumentType
)

from config import (
    FILEPATH_LOGGER,
    DIR_CSV_1DAY,
    DIR_CSV_1MIN
)
from src.exceptions import IncorrectFirstCandle
from src.api_calls import get_candles, get_shares
from src.date_utils import DateTimeFactory, dtf, TZ_UTC
from src.my_logging import get_logger, log_and_exit
from src.csv_candles import CSVCandles
from src.schemas import (
    Candle,
    CSVCandlesStatus
)


async def get_or_read_candles(
        instrument: Instrument,
        from_: datetime,
        to: datetime,
        interval: CandleInterval,
        delta: timedelta
) -> list[Candle]:
    from_, to = await configure_datetime_range(instrument, from_=from_, to=to)
    filepath = _get_instrument_filepath(instrument, interval=interval)
    csv = CSVCandles(filepath)
    status_before = None

    while True:
        try:
            status, *r = await csv.status(from_=from_, to=to, interval=interval)
        except Exception as e:
            logging.error(f'{filepath=}')
            log_and_exit(e)

        ms = f'ticker_figi: "{instrument.ticker}_{instrument.figi}" | StatusHistoryInCSV: '
        if status == status_before:
            if status == CSVCandlesStatus.NEED_INSERT:
                raise IncorrectFirstCandle(f'{r[0]=} | {from_=}')
            raise Exception(f'Same {status=} | {ms}')
        if status_before is None:
            status_before = status

        match status:
            case CSVCandlesStatus.OK:
                logging.info(ms + 'OK')
                return r[0]
            case CSVCandlesStatus.NOT_EXISTS:
                logging.info(ms + 'not_exists')
                await csv.prepare_new()
                candles = await get_candles(instrument.figi, from_=from_, to=to, interval=interval, delta=delta)
                await csv.append(candles)
                return candles
            case CSVCandlesStatus.NEED_APPEND:
                from_temp, candles_from_file = r
                logging.info(ms + f'need_append. from_temp={dtf.datetime_strf(from_temp)} | to={dtf.datetime_strf(to)}')
                # 1st candle in response is last candle in file
                candles = (await get_candles(instrument.figi, from_=from_temp, to=to,
                                             interval=interval, delta=delta))[1:]
                if candles:
                    await csv.append(candles)
                return candles_from_file + candles
            case CSVCandlesStatus.NEED_INSERT:
                to_temp = r[0]
                logging.info(ms + f'need_insert. from={dtf.datetime_strf(from_)} |'
                                  f' to_temp={dtf.datetime_strf(to_temp)}')
                candles_ = await get_candles(instrument.figi, from_=from_, to=to_temp, interval=interval, delta=delta)
                # 1st candle in file is last candle in get_candles response
                await csv.insert(candles_[:-1])
            # case CSVCandlesStatus.FIGI_CHANGED:
            #     logging.info(ms + 'figi_changed')
            #     raise NotImplementedError
            # case CSVCandlesStatus.TICKER_CHANGED:
            #     logging.info(ms + 'ticker_changed')
            #     raise NotImplementedError


async def configure_datetime_range(instrument: Instrument, from_: datetime, to: datetime) \
        -> tuple[datetime, datetime]:
    is_from_defined, is_to_defined = False, False
    from_ = from_.replace(hour=0, minute=0, second=0, microsecond=0)
    delta = timedelta(days=15)

    logging.info(f'figi={instrument.figi} | 1day candle={instrument.first_1day_candle_date}')
    if from_ < instrument.first_1min_candle_date:
        logging.warning(f'ticker={instrument.ticker} from_={dtf.datetime_strf(from_)} < first_1min_candle='
                        f'{dtf.datetime_strf(instrument.first_1min_candle_date)}. ')
        from_ = instrument.first_1min_candle_date
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


async def get_all_instrument_history(instrument: Instrument, interval: CandleInterval) -> list[Candle]:
    """ First time downloading history """

    if interval == CandleInterval.CANDLE_INTERVAL_1_MIN:
        from_ = instrument.first_1min_candle_date
        delta = timedelta(days=1)
    elif interval == CandleInterval.CANDLE_INTERVAL_DAY:
        delta = timedelta(days=365)
        from_ = instrument.first_1day_candle_date
    else:
        raise Exception(f'Unexpected {interval=} for downloading history')

    to = DateTimeFactory.now()
    return await get_or_read_candles(instrument=instrument, from_=from_, to=to, interval=interval, delta=delta)


async def download_existing_instruments_by_type(instruments_type: InstrumentType, interval: CandleInterval) -> None:
    match instruments_type:
        case InstrumentType.INSTRUMENT_TYPE_SHARE:
            instruments = await get_shares()
        case _:
            raise NotImplementedError

    for i, instrument in enumerate(instruments):
        if instrument.figi in ['TCS00A106YF0']:
            logging.info(f'Skipped {instrument.ticker=} | {instrument.figi=}')
            continue
        try:
            candles = await get_all_instrument_history(instrument=instrument, interval=interval)
            logging.info(f'{i}/{len(instruments)} | {instrument.ticker} downloaded | {len(candles)=} | {interval=}')
        except IncorrectFirstCandle as e:
            logging.warning(e, exc_info=True)


def _get_instrument_filepath(instrument: Instrument, interval: CandleInterval) -> Path:
    match interval:
        case interval.CANDLE_INTERVAL_1_MIN:
            dir_ = DIR_CSV_1MIN
        case interval.CANDLE_INTERVAL_DAY:
            dir_ = DIR_CSV_1DAY
        case _:
            raise Exception(f'Unexpected {interval=}')

    return dir_ / f'{instrument.ticker}_{instrument.figi}.csv'


async def main():
    from tinkoff.invest import InstrumentIdType
    from src.api_calls import get_instrument_by

    # instrument = await get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=FIGI)
    # await get_all_instrument_history(instrument=instrument, interval=CandleInterval.CANDLE_INTERVAL_DAY)


if __name__ == "__main__":
    import asyncio
    get_logger(FILEPATH_LOGGER)
    asyncio.run(main())