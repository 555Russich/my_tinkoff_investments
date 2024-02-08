import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from tinkoff.invest import (
    CandleInterval,
    Instrument,
    InstrumentType
)

from config import DIR_CANDLES_1MIN, DIR_CANDLES_1DAY # noqa
from my_tinkoff.schemas import Candle, Candles, CSVCandlesStatus
from my_tinkoff.helpers import configure_datetime_range
from my_tinkoff.date_utils import dt_form_sys, DateTimeFactory
from my_tinkoff.api_calls.market_data import get_candles
from my_tinkoff.api_calls.instruments import get_shares
from my_tinkoff.exceptions import (
    IncorrectFirstCandle,
    UnexpectedCandleInterval
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
        from_, to = await configure_datetime_range(instrument, from_=from_, to=to, interval=interval)
        filepath = cls.get_filepath(instrument, interval=interval)
        csv = cls(filepath)
        status_before = None

        while True:
            try:
                status, *r = await csv._status(from_=from_, to=to, interval=interval)
            except Exception as ex:
                logging.error(f'{filepath=}')
                raise ex

            ms = f'{instrument.ticker=} | {instrument.uid=} | StatusHistoryInCSV: '
            if status == status_before:
                if status == CSVCandlesStatus.NEED_INSERT:
                    raise IncorrectFirstCandle(f'{r[0]=} | {from_=}')
                raise Exception(f'Same {status=} | {ms}')
            if status_before is None:
                status_before = status

            match status:
                case CSVCandlesStatus.OK:
                    logging.debug(ms + 'OK')
                    return r[0]
                case CSVCandlesStatus.NOT_EXISTS:
                    logging.debug(ms + 'not_exists')
                    await csv._prepare_new()
                    candles = await get_candles(instrument.figi, from_=from_, to=to, interval=interval)
                    await csv._append(candles)
                    return Candles(candles)
                case CSVCandlesStatus.NEED_APPEND:
                    from_temp, candles_from_file = r
                    logging.debug(f'{ms} need_append. from_temp={dt_form_sys.datetime_strf(from_temp)} | '
                                  f'to={dt_form_sys.datetime_strf(to)}')
                    # 1st candle in response is last candle in file
                    candles = (await get_candles(instrument.figi, from_=from_temp, to=to, interval=interval))[1:]

                    # append to file only completed candles
                    complete_candles = Candles([c for c in candles if c.is_complete])
                    if complete_candles:
                        await csv._append(complete_candles)

                    return candles_from_file + candles
                case CSVCandlesStatus.NEED_INSERT:
                    to_temp = r[0]
                    logging.debug(f'{ms} need_insert. from={dt_form_sys.datetime_strf(from_)} | '
                                  f'to_temp={dt_form_sys.datetime_strf(to_temp)}')
                    candles_ = await get_candles(instrument.figi, from_=from_, to=to_temp, interval=interval)
                    # 1st candle in file is last candle in get_candles response
                    await csv._insert(candles_[:-1])

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
    async def get_all_instruments_by_type(cls, instruments_type: InstrumentType, interval: CandleInterval) -> None:
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

    async def _append(self, candles: Candles) -> None:
        if not candles:
            return
        candles = candles.remove_same_candles_in_a_row()

        data = NEW_LINE.join(
            DELIMITER.join(
                str(v) for v in (candle.open, candle.high, candle.low, candle.close, candle.volume, candle.time)
            ) for candle in candles
        ) + NEW_LINE

        with open(self.filepath, 'a') as f:
            f.write(data)

    async def _insert(self, candles: Candles):
        with open(self.filepath, 'r') as f:
            data = f.readlines()

        await self._prepare_new()
        await self._append(candles)
        with open(self.filepath, 'a') as f:
            f.writelines(data[1:])

    async def _read(self, from_: datetime, to: datetime, interval: CandleInterval) -> tuple:
        candles = Candles()

        with open(self.filepath, 'r') as f:
            data = f.readlines()
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

                if i == 0 and candle.time > from_:
                    if not interval == interval.CANDLE_INTERVAL_DAY and candle.time.date() == from_.date():
                        return CSVCandlesStatus.NEED_INSERT, candle.time
                if i == len(data) - 1 and candle.time < to:
                    if not interval == interval.CANDLE_INTERVAL_DAY:
                        return CSVCandlesStatus.NEED_APPEND, candle.time, candles

                if from_ <= candle.time <= to:
                    candles.append(candle)

        return CSVCandlesStatus.OK, candles

    async def _prepare_new(self):
        with open(self.filepath, 'w') as f:
            f.write(DELIMITER.join(COLUMNS) + NEW_LINE)

    async def _status(self, from_: datetime, to: datetime, interval: CandleInterval) -> tuple[CSVCandlesStatus, Any]:
        if not self.filepath.exists():
            return CSVCandlesStatus.NOT_EXISTS, None

        return await self._read(from_, to, interval=interval)

    @classmethod
    def get_filepath(cls, instrument: Instrument, interval: CandleInterval) -> Path:
        match interval:
            case interval.CANDLE_INTERVAL_1_MIN:
                dir_ = DIR_CANDLES_1MIN
            case interval.CANDLE_INTERVAL_DAY:
                dir_ = DIR_CANDLES_1DAY
            case _:
                raise UnexpectedCandleInterval(f'{interval=}')

        return dir_ / f'{instrument.uid}.csv'


