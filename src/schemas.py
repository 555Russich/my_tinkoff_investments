from dataclasses import dataclass
from datetime import datetime
from collections import UserList
from typing import Self

from tinkoff.invest import Instrument
from backtrader import Trade


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
        from src.exceptions import IncorrectDatetimeConsistency

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


@dataclass
class TradeSignalType:
    UNDEFINED = -1
    VOLUME = 1
    PRICE = 2
    VOLUME_AND_PRICE = 3


@dataclass
class StrategyResult:
    instrument: Instrument
    start_cash: float
    trades: list[Trade] = None
    sharpe_ratio: float | None = None

    def __repr__(self) -> str:
        return (
            f'Ticker: {self.instrument.ticker}\n'
            f'PnL: {round(self.pnlcomm, 2)} {self.instrument.currency.upper()} | {round(self.pnlcomm_percent*100, 2)}%\n'
            f'{self.count_successful_trades}/{len(self.trades)} successful trades | {round(self.percent_successful_trades*100, 2) if self.percent_successful_trades else None}%\n'
            f'Sharpe Ratio: {round(self.sharpe_ratio, 2) if self.sharpe_ratio else None}'
        )

    @property
    def pnlcomm(self) -> float:
        return sum(t.pnlcomm for t in self.trades)

    @property
    def pnlcomm_percent(self) -> float:
        return self.pnlcomm / self.start_cash

    @property
    def count_successful_trades(self) -> int:
        return len([1 for t in self.trades if t.pnlcomm > 0])

    @property
    def percent_successful_trades(self) -> float | None:
        if len(self.trades):
            return self.count_successful_trades / len(self.trades)


class StrategiesResults(UserList[StrategyResult]):

    def __repr__(self) -> str:
        return (
            f'Cumulative of {len(self)} strategies results\n'
            f'PnL: {round(self.pnlcomm, 2)} | {round(self.pnlcomm_percent*100, 2)}%\n'
            f'{self.count_successful_trades}/{len(self.trades)} successful trades | {round(self.percent_successful_trades*100, 2) if self.percent_successful_trades else None}%\n'
            f'Average Sharpe Ratio: {round(self.sharpe_ratio, 2) if self.sharpe_ratio else None}'
        )

    @property
    def pnlcomm(self) -> float:
        return sum([r.pnlcomm for r in self])

    @property
    def pnlcomm_percent(self) -> float:
        return sum([r.pnlcomm_percent for r in self])

    @property
    def trades(self) -> list[Trade]:
        return [t for r in self for t in r.trades]

    @property
    def count_successful_trades(self) -> int:
        return len([1 for t in self.trades if t.pnlcomm > 0])

    @property
    def percent_successful_trades(self) -> float | None:
        if self.trades:
            return self.count_successful_trades / len(self.trades)

    @property
    def sharpe_ratio(self) -> float | None:
        sharpe_ratios = [r.sharpe_ratio for r in self if r.sharpe_ratio]
        if sharpe_ratios:
            return sum(sharpe_ratios) / len(sharpe_ratios)
