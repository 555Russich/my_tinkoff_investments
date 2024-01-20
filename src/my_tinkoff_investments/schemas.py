from dataclasses import dataclass
from datetime import datetime
from collections import UserList
from typing import Self


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: int
    time: datetime
    is_complete: bool | None = None


class Candles(UserList[Candle]):
    def check_datetime_consistency(self) -> None:
        from my_tinkoff_investments.exceptions import IncorrectDatetimeConsistency

        for i in range(1, len(self)):
            if self[i-1].time > self[i].time:
                raise IncorrectDatetimeConsistency(f'Previous candle datetime value later than previous candle has: '
                                                   f'{self[i-1].time=} | {self[i].time=}')

    def remove_same_candles_in_a_row(self) -> Self:
        new_candles = Candles()
        c1 = self[0]
        for i in range(1, len(self)):
            c2 = self[i]
            if not (c1.open == c2.open and c1.high == c2.high and c1.low == c2.low and
                    c1.close == c2.close and c1.volume == c2.volume and c1.time != c2.time):
                new_candles.append(c1)
                c1 = c2

        new_candles.append(self[-1])
        return new_candles


@dataclass(frozen=True, init=False)
class CSVCandlesStatus:
    UNDEFINED = -1
    OK = 0
    NOT_EXISTS = 1
    NEED_APPEND = 2
    NEED_INSERT = 3
    TICKER_CHANGED = 5
    FIGI_CHANGED = 6
