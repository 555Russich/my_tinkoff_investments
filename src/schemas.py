from dataclasses import dataclass
from datetime import datetime
from collections import UserList

from tinkoff.invest import Instrument
# import pandas as pd


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
    # def df(self) -> pd.DataFrame:
    #     df = pd.DataFrame([{k.capitalize(): v for k, v in c.__dict__.items()} for c in self])
    #     #df['Time'] = pd.DatetimeIndex(df['Time'])
        # return df
    pass


@dataclass(frozen=True, init=False)
class CSVCandlesStatus:
    UNDEFINED = -1
    OK = 0
    NOT_EXISTS = 1
    NEED_APPEND = 2
    NEED_INSERT = 3
    TICKER_CHANGED = 5
    FIGI_CHANGED = 6


@dataclass
class TradeSignalType:
    UNDEFINED = -1
    VOLUME = 1
    PRICE = 2
    VOLUME_AND_PRICE = 3


@dataclass
class StrategyResult:
    instrument: Instrument | None = None
    percent: float = 0
    count_deals: int = 0
    count_successful_deals: int = 0

