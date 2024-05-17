import logging
from pathlib import Path
from datetime import datetime, timedelta

from tinkoff.invest import (
    Instrument,
    InstrumentType
)
from tinkoff.invest import CandleInterval as TinkoffCandleInterval

from config import DIR_CANDLES # noqa
from trading_helpers.schemas import AnyCandle, CandleInterval

from my_tinkoff.schemas import Candle, Candles
from my_tinkoff.helpers import configure_datetime_from
from my_tinkoff.date_utils import dt_form_sys
from my_tinkoff.api_calls.market_data import get_candles

from trading_helpers.csv_candles import _CSVCandles, Interval
from trading_helpers.exceptions import (
    UnexpectedCandleInterval,
    IncorrectFirstCandle,
    CSVCandlesNeedAppend,
    CSVCandlesNeedInsert
)


class CSVCandles(_CSVCandles):
    CANDLE = Candle
    CANDLES = Candles
    COLUMNS = {
        'open': float,
        'high': float,
        'low': float,
        'close': float,
        'volume': int,
        'dt': datetime.fromisoformat
    }

    DIR_API = DIR_CANDLES / 'tinkoff'
    DIR_API.mkdir(exist_ok=True)

    @classmethod
    async def download_or_read(
            cls,
            instrument: Instrument,
            from_: datetime,
            to: datetime,
            interval: CandleInterval,
    ) -> Candles:
        candles = None
        from_ = configure_datetime_from(from_=from_, instrument=instrument, interval=interval)
        csv = cls(instrument_id=instrument.uid, interval=interval)

        if not csv.filepath.exists():
            logging.debug(f'File not exists | ticker={instrument.ticker} | uid={instrument.uid}')
            await csv._prepare_new()
            candles = await get_candles(instrument_id=instrument.uid, from_=from_, to=to, interval=interval)
            await csv._append(candles)
            return candles

        for retry in range(1, 4):
            try:
                return await csv._read(from_=from_, to=to, interval=csv.interval)
            except CSVCandlesNeedAppend as ex:
                logging.debug(f'Need append | {retry=} | ticker={instrument.ticker} | uid={instrument.uid} | from_temp='
                              f'{dt_form_sys.datetime_strf(ex.from_temp)} | to={dt_form_sys.datetime_strf(to)}')
                # 1st candle in response is last candle in file
                candles = (await get_candles(instrument_id=instrument.uid, from_=ex.from_temp, to=to, interval=interval))[1:]

                if not candles or (len(candles) == 1 and candles[0].is_complete is False):
                    to = ex.candles[-1].dt if to > ex.candles[-1].dt else to

                if candles:
                    candles = candles if candles[-1].is_complete else candles[:-1]
                    await csv._append(candles)
            except CSVCandlesNeedInsert as ex:
                logging.debug(f'Need insert | {retry=} | ticker={instrument.ticker} | uid={instrument.uid} |'
                              f' from={dt_form_sys.datetime_strf(from_)} | '
                              f'to_temp={dt_form_sys.datetime_strf(ex.to_temp)}')
                if retry == 3:
                    raise IncorrectFirstCandle(f'{candles[0].dt=} | {from_=}')

                candles = await get_candles(instrument_id=instrument.uid, from_=from_, to=ex.to_temp, interval=interval)
                # 1st candle in file is last candle in get_candles response
                candles = candles[:-1]

                if candles:
                    await csv._insert(candles[:-1])
                else:
                    logging.debug(f'Nothing between from_={dt_form_sys.datetime_strf(from_)} and to_temp='
                                  f'{dt_form_sys.datetime_strf(ex.to_temp)}')
                    from_ = ex.to_temp
            except Exception as ex:
                logging.error(f'{retry=} | {csv.filepath} | {instrument.ticker=}\n{ex}', exc_info=True)
                raise ex

    @classmethod
    def row2candle(cls, row: list[float | int | datetime]) -> AnyCandle:
        row.append(True)  # is_complete=True
        return cls.CANDLE(*row)

    @classmethod
    def convert_candle_interval(cls, interval: Interval) -> CandleInterval:
        match interval:
            case TinkoffCandleInterval.CANDLE_INTERVAL_1_MIN:
                i = CandleInterval.MIN_1
            case TinkoffCandleInterval.CANDLE_INTERVAL_2_MIN:
                i = CandleInterval.MIN_2
            case TinkoffCandleInterval.CANDLE_INTERVAL_3_MIN:
                i = CandleInterval.MIN_3
            case TinkoffCandleInterval.CANDLE_INTERVAL_5_MIN:
                i = CandleInterval.MIN_5
            case TinkoffCandleInterval.CANDLE_INTERVAL_10_MIN:
                i = CandleInterval.MIN_10
            case TinkoffCandleInterval.CANDLE_INTERVAL_15_MIN:
                i = CandleInterval.MIN_15
            case TinkoffCandleInterval.CANDLE_INTERVAL_30_MIN:
                i = CandleInterval.MIN_30
            case TinkoffCandleInterval.CANDLE_INTERVAL_HOUR:
                i = CandleInterval.HOUR
            case TinkoffCandleInterval.CANDLE_INTERVAL_2_HOUR:
                i = CandleInterval.HOUR_2
            case TinkoffCandleInterval.CANDLE_INTERVAL_4_HOUR:
                i = CandleInterval.HOUR_4
            case TinkoffCandleInterval.CANDLE_INTERVAL_DAY:
                i = CandleInterval.DAY
            case TinkoffCandleInterval.CANDLE_INTERVAL_WEEK:
                i = CandleInterval.WEEK
            case TinkoffCandleInterval.CANDLE_INTERVAL_MONTH:
                i = CandleInterval.MONTH
            case _:
                raise UnexpectedCandleInterval(str(interval))
        return i
