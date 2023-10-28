import logging
from pathlib import Path
from datetime import datetime
from typing import Any

import aiofiles
from tinkoff.invest import CandleInterval

from src.schemas import Candle, CSVCandlesStatus

COLUMNS_HISTORY_CSV = ('open', 'high', 'low', 'close', 'volume', 'time')
DELIMITER = ';'
NEW_LINE = '\n'


class CSVCandles:
    def __init__(self, filepath: Path):
        self.filepath = filepath

    async def append(self, candles: list[Candle]) -> None:
        async with aiofiles.open(self.filepath, 'a') as f:
            await f.write(NEW_LINE.join(
                DELIMITER.join(str(v) for v in (candle.open, candle.high, candle.low,
                                                candle.close, candle.volume, candle.time))
                for candle in candles
            ) + NEW_LINE)

    async def insert(self, candles: list[Candle]):
        async with aiofiles.open(self.filepath, 'r') as f:
            data = await f.readlines()

        await self.prepare_new()
        await self.append(candles)
        async with aiofiles.open(self.filepath, 'a') as f:
            await f.writelines(data[1:])

    async def read(self, from_: datetime, to: datetime, interval: CandleInterval) -> tuple:
        candles = []

        async with aiofiles.open(self.filepath, 'r') as f:
            data = await f.readlines()
            columns = data[0].replace(NEW_LINE, '').split(DELIMITER)
            data = data[1:]

            for i, row in enumerate(data):
                str_values = row.replace(NEW_LINE, '').split(DELIMITER)
                values = []

                for column, value in zip(columns, str_values):
                    match column:
                        case c if c in ('open', 'high', 'low', 'close'):
                            values.append(float(value))
                        case 'volume':
                            values.append(int(value))
                        case 'time':
                            # try:
                            values.append(datetime.fromisoformat(value))
                            # except ValueError:
                            #     self.filepath.unlink()
                            #     return CSVCandlesStatus.NOT_EXISTS, None

                candle = Candle(*values)

                if i == 0 and candle.time > from_:
                    if not (interval.CANDLE_INTERVAL_DAY and candle.time.date() == from_.date()):
                        return CSVCandlesStatus.NEED_INSERT, candle.time
                if i == len(data) - 1 and candle.time < to:
                    if not (interval.CANDLE_INTERVAL_DAY and candle.time.date() == to.date()):
                        return CSVCandlesStatus.NEED_APPEND, candle.time, candles

                if from_ <= candle.time <= to:
                    candles.append(candle)

        return CSVCandlesStatus.OK, candles

    async def prepare_new(self):
        async with aiofiles.open(self.filepath, 'w') as f:
            await f.write(DELIMITER.join(COLUMNS_HISTORY_CSV) + NEW_LINE)

    async def status(self, from_: datetime, to: datetime, interval: CandleInterval) -> tuple[CSVCandlesStatus, Any]:
        if not self.filepath.exists():
            # ticker, figi = self.filepath.stem.split('_')
            # for filepath_ in self.filepath.parent.iterdir():
            #     ticker_, figi_ = filepath_.stem.split('_')
            #     if ticker == ticker_:
            #         return CSVCandlesStatus.TICKER_CHANGED, ticker
            #     elif figi == figi_:
            #         return CSVCandlesStatus.FIGI_CHANGED, figi
            return CSVCandlesStatus.NOT_EXISTS, None

        return await self.read(from_, to, interval=interval)
