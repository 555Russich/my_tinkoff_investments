import logging
from pathlib import Path
from datetime import datetime, timedelta

from tinkoff.invest import (
    CandleInterval,
    Instrument,
    InstrumentType
)
import aiofiles

from config import DIR_CANDLES_1MIN, DIR_CANDLES_1DAY # noqa
from my_tinkoff.schemas import Candle, Candles
from my_tinkoff.helpers import configure_datetime_from
from my_tinkoff.date_utils import dt_form_sys, DateTimeFactory
from my_tinkoff.api_calls.market_data import get_candles
from my_tinkoff.api_calls.instruments import get_shares
from my_tinkoff.exceptions import (
    IncorrectFirstCandle,
    UnexpectedCandleInterval,
    CSVCandlesNeedInsert,
    CSVCandlesNeedAppend,
)


COLUMNS = ('open', 'high', 'low', 'close', 'volume', 'time')
DELIMITER = ';'
NEW_LINE = '\n'


class CSVCandles:
    def __init__(self, filepath: Path):
        self.filepath = filepath

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

        filepath = cls.get_filepath(instrument, interval=interval)
        csv = cls(filepath)

        if not filepath.exists():
            logging.debug(f'File not exists | ticker={instrument.ticker} | uid={instrument.uid}')
            await csv._prepare_new()
            candles = await get_candles(instrument_id=instrument.uid, from_=from_, to=to, interval=interval)
            await csv._append(candles)
            return candles

        for retry in range(1, 4):
            try:
                return await csv._read(from_=from_, to=to, interval=interval)
            except CSVCandlesNeedAppend as ex:
                logging.debug(f'Need append | {retry=} | ticker={instrument.ticker} | uid={instrument.uid} | from_temp='
                              f'{dt_form_sys.datetime_strf(ex.from_temp)} | to={dt_form_sys.datetime_strf(to)}')
                # 1st candle in response is last candle in file
                candles = (await get_candles(instrument_id=instrument.uid, from_=ex.from_temp, to=to, interval=interval))[1:]

                if not candles or (len(candles) == 1 and candles[0].is_complete is False):
                    to = ex.candles[-1].time if to > ex.candles[-1].time else to

                if candles:
                    candles = candles if candles[-1].is_complete else candles[:-1]
                    await csv._append(candles)
            except CSVCandlesNeedInsert as ex:
                logging.debug(f'Need insert | {retry=} | ticker={instrument.ticker} | uid={instrument.uid} |'
                              f' from={dt_form_sys.datetime_strf(from_)} | '
                              f'to_temp={dt_form_sys.datetime_strf(ex.to_temp)}')
                if retry == 3:
                    raise IncorrectFirstCandle(f'{candles[0].time=} | {from_=}')

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
    async def get_all_instrument_history(cls, instrument: Instrument, interval: CandleInterval) -> Candles:
        """ First time downloading history """

        if interval == CandleInterval.CANDLE_INTERVAL_1_MIN:
            from_ = instrument.first_1min_candle_date
        elif interval == CandleInterval.CANDLE_INTERVAL_DAY:
            from_ = instrument.first_1day_candle_date
        else:
            raise Exception(f'Unexpected {interval=} for downloading history')

        return await CSVCandles.download_or_read(
            instrument=instrument, from_=from_, to=DateTimeFactory.now(), interval=interval)

    @classmethod
    async def get_all_instruments_histories_by_type(
            cls,
            instruments_type: InstrumentType,
            interval: CandleInterval
    ) -> None:
        match instruments_type:
            case InstrumentType.INSTRUMENT_TYPE_SHARE:
                instruments = await get_shares()
            case _:
                raise NotImplementedError

        for i, instrument in enumerate(instruments):
            if instrument.figi in ['TCS00A106YF0']:
                logging.debug(f'Skipped {instrument.ticker=} | {instrument.uid=}')
                continue
            try:
                candles = await cls.get_all_instrument_history(instrument=instrument, interval=interval)
                logging.debug(f'{i}/{len(instruments)} | {instrument.uid=} downloaded | {len(candles)=} | {interval=}')
            except IncorrectFirstCandle as e:
                logging.warning(e, exc_info=True)

    @classmethod
    def get_filepath(cls, instrument: Instrument, interval: CandleInterval) -> Path:
        if interval == CandleInterval.CANDLE_INTERVAL_1_MIN:
            dir_ = DIR_CANDLES_1MIN
        elif interval == CandleInterval.CANDLE_INTERVAL_DAY:
            dir_ = DIR_CANDLES_1DAY
        else:
            raise UnexpectedCandleInterval(f'{interval=}')

        return dir_ / f'{instrument.uid}.csv'

    async def _read(self, from_: datetime, to: datetime, interval: CandleInterval) -> Candles:
        candles = Candles()

        async with aiofiles.open(self.filepath, 'r') as f:
            data = await f.readlines()

        columns = data[0].replace(NEW_LINE, '').split(DELIMITER)
        data = data[1:]

        for i, row in enumerate(data):
            str_values = row.replace(NEW_LINE, '').split(DELIMITER)
            values = []

            for column, value in zip(columns, str_values):
                if column in ('open', 'high', 'low', 'close'):
                    values.append(float(value))
                elif column == 'volume':
                    values.append(int(value))
                elif column == 'time':
                    values.append(datetime.fromisoformat(value))

            candle = Candle(*values, is_complete=True)
            if from_ <= candle.time <= to:
                candles.append(candle)

            if i == 0 and candle.time > from_:
                if not (interval == CandleInterval.CANDLE_INTERVAL_DAY and candle.time.date() == from_.date()):
                    raise CSVCandlesNeedInsert(to_temp=candle.time)
            if i == len(data) - 1 and candle.time < to:
                dt_delta = to - candle.time
                if (
                        (
                                candle.time.date() == to.date() and
                                interval == CandleInterval.CANDLE_INTERVAL_1_MIN and dt_delta > timedelta(minutes=1+1) or
                                interval == CandleInterval.CANDLE_INTERVAL_5_MIN and dt_delta > timedelta(minutes=5+1) or
                                interval == CandleInterval.CANDLE_INTERVAL_HOUR and dt_delta > timedelta(minutes=60+1)
                        ) or
                        (candle.time.date() < to.date() and interval == CandleInterval.CANDLE_INTERVAL_DAY)
                ):
                    raise CSVCandlesNeedAppend(from_temp=candle.time, candles=candles)
        return candles

    async def _append(self, candles: Candles) -> None:
        if not candles:
            return

        data = NEW_LINE.join(
            DELIMITER.join(
                str(v) for v in (candle.open, candle.high, candle.low, candle.close, candle.volume, candle.time)
            ) for candle in candles
        ) + NEW_LINE

        async with aiofiles.open(self.filepath, 'a') as f:
            await f.write(data)

    async def _insert(self, candles: Candles):
        async with aiofiles.open(self.filepath, 'r') as f:
            data = await f.readlines()

        await self._prepare_new()
        await self._append(candles)
        async with aiofiles.open(self.filepath, 'a') as f:
            await f.writelines(data[1:])

    async def _prepare_new(self):
        async with aiofiles.open(self.filepath, 'w') as f:
            await f.write(DELIMITER.join(COLUMNS) + NEW_LINE)
