from pathlib import Path
from datetime import datetime
from typing import Any

import aiofiles

from src.schemas import MyHistoricCandle, StatusHistoryInCSV

COLUMNS_HISTORY_CSV = ('open', 'high', 'low', 'close', 'volume', 'time')


async def append_candles(filepath: Path, candles: list[MyHistoricCandle]):
    async with aiofiles.open(filepath, 'a') as f:
        await f.write('\n'.join(
            ';'.join(str(v) for v in (candle.open, candle.high, candle.low, candle.close, candle.volume, candle.time))
            for candle in candles
        ) + '\n')


async def insert_candles(filepath: Path, candles: list[MyHistoricCandle]):
    async with aiofiles.open(filepath, 'r') as f:
        data = await f.readlines()

    await prepare_new_csv(filepath)
    await append_candles(filepath, candles)
    async with aiofiles.open(filepath, 'a') as f:
        await f.writelines(data[1:])

from line_profiler_pycharm import profile
@profile
async def read_candles(filepath: Path, from_: datetime, to: datetime) -> tuple:
    candles = []

    async with aiofiles.open(filepath, 'r') as f:
        data = await f.readlines()
        columns = data[0].replace('\n', '').split(';')
        data = data[1:]

        for i, row in enumerate(data):
            str_values = row.replace('\n', '').split(';')
            values = []

            for column, value in zip(columns, str_values):
                match column:
                    case c if c in ('open', 'high', 'low', 'close'):
                        values.append(float(value))
                    case 'volume':
                        values.append(int(value))
                    case 'time':
                        values.append(datetime.fromisoformat(value))
            candle = MyHistoricCandle(*values)

            match i:
                case 0 if candle.time > from_:
                    return StatusHistoryInCSV.NEED_INSERT, candle.time
                case x if x == len(data) - 1 and candle.time < to:
                    return StatusHistoryInCSV.NEED_APPEND, candle.time, candles

            if from_ <= candle.time <= to:
                candles.append(candle)

    assert candles != [], f'{filepath}'
    return StatusHistoryInCSV.OK, candles


async def prepare_new_csv(filepath: Path):
    async with aiofiles.open(filepath, 'w') as f:
        await f.write(';'.join(COLUMNS_HISTORY_CSV) + '\n')


async def get_csv_status(filepath: Path, from_: datetime, to: datetime) -> tuple[StatusHistoryInCSV, Any]:
    if not filepath.exists():
        ticker, figi = filepath.stem.split('_')
        for filepath_ in filepath.parent.iterdir():
            if ticker in filepath_.stem:
                return StatusHistoryInCSV.TICKER_CHANGED, ticker
            elif figi in filepath_.stem:
                return StatusHistoryInCSV.FIGI_CHANGED, figi
        return StatusHistoryInCSV.NOT_EXISTS, None

    return await read_candles(filepath, from_, to)
