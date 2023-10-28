from dataclasses import dataclass
from datetime import datetime

from tinkoff.invest import Instrument


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: int
    time: datetime
    is_complete: bool | None = None


@dataclass(frozen=True)
class TempCandles:
    candles: list[Candle]
    from_: datetime
    to: datetime


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
