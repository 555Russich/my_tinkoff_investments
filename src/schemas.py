from dataclasses import dataclass
from datetime import datetime

from tinkoff.invest import (
    Share,
    Dividend
)


@dataclass(frozen=True)
class MyHistoricCandle:
    open: float
    high: float
    low: float
    close: float
    volume: int
    time: datetime
    is_complete: bool | None = None


@dataclass(frozen=True, init=False)
class StatusHistoryInCSV:
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
class DivShare:
    share: Share
    dividends: list[Dividend]

    @property
    def last_payment_date(self) -> datetime:
        ...
