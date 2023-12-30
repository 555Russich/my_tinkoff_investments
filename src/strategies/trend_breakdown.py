import asyncio
import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
    TradeDirection,
    InstrumentIdType,
    CandleInterval, Instrument,
)
import backtrader as bt

from config import FILEPATH_LOGGER
from src.my_logging import get_logger
from src.date_utils import DateTimeFactory, dt_form_sys
from src.api_calls.instruments import get_instrument_by
from src.csv_candles import CSVCandles
from src.backtrader.csv_data import MyCSVData
from src.schemas import StrategyResult, StrategiesResults
from src.instruments.shares import Shares
from src.exceptions import IncorrectDatetimeConsistency

get_logger(FILEPATH_LOGGER)


class StrategyLongTrendBreakDown(bt.Strategy):
    def __init__(self, min_count_bars: int | None = None):
        self.order = None
        self.limit_order = None
        self.trades: list[bt.Trade] = []
        self.closes: bt.LineBuffer = self.datas[0].close
        self.opens: bt.LineBuffer = self.datas[0].open
        self.highs = self.datas[0].high
        self.lows = self.datas[0].low

        self.changes: bt.linebuffer.LinesOperation = self.closes - self.opens  # noqa
        self.min_count_bars = min_count_bars
        self.max_count_bars = 0

    def get_max_size(self, price: float) -> int:
        return self.broker.get_value() // price

    def log(self, txt: str, dt: datetime | None = None):
        if dt is None:
            dt = self.datas[0].datetime.datetime(0)

        dt = dt_form_sys.datetime_strf(dt)
        logging.info(f'{{{dt}}} {{{txt}}}')

    def notify_order(self, order: bt.Order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'Buy executed | Price={order.executed.price} | Cost={order.executed.value} | '
                         f'Comm={order.executed.comm}')
            elif order.issell():
                self.log(f'Sell executed | Price={order.executed.price} | Cost={order.executed.value} | '
                         f'Comm={order.executed.comm}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order status: {order.Status[order.status]}')

        # no pending order
        self.order = None

    def notify_trade(self, trade: bt.Trade):
        if trade.isclosed:
            self.trades.append(trade)
            self.log(f'{trade.pnl=} | {trade.pnlcomm=}')

    def next(self):
        if len(self.closes) <= self.min_count_bars:
            return

        if self.position:
            if self.position.size < 0:
                self.buy(size=self.position.size)
            elif self.position.size > 0:
                self.sell(size=self.position.size)

            if self.limit_order:
                self.broker.cancel(self.limit_order)
                self.limit_order = None

        if dt_form_sys.datetime_strf(self.datas[0].datetime.datetime(0)) == '02.06.2009 23:59:59':
            pass

        changes = self.changes.get(ago=-1, size=len(self.closes)-1)
        count_bars_in_a_row, trend_direction = self.get_count_bars_in_a_row_with_direction(changes)

        if count_bars_in_a_row < self.min_count_bars:
            return
        elif count_bars_in_a_row > self.max_count_bars:
            self.max_count_bars = count_bars_in_a_row
            self.log(f'Updating {self.max_count_bars=}')

        # spec_count_bars = int(self.max_count_bars * 0.5)
        spec_count_bars = self.min_count_bars

        if spec_count_bars <= count_bars_in_a_row >= self.min_count_bars:
            self.log(f'{count_bars_in_a_row=} | {spec_count_bars=}')
            order_size = self.get_max_size(self.closes[0]) // 2
            if trend_direction == TradeDirection.TRADE_DIRECTION_BUY and self.changes[0] < 0:
                self.order = self.sell(size=order_size)
                # order_price = self.closes[0] - self.closes[0] * 0.01
                # print(f'{order_price=}')
                # self.limit_order = self.buy(exectype=bt.Order.Limit, price=order_price)
            elif trend_direction == TradeDirection.TRADE_DIRECTION_SELL and self.changes[0] > 0:
                self.order = self.buy(size=order_size)
                # order_price = self.closes[0] + self.closes[0] * 0.01
                # print(f'{order_price=}')
                # self.limit_order = self.sell(exectype=bt.Order.Limit, price=order_price)

    def get_count_bars_in_a_row_with_direction(self, changes: list) -> tuple[int, TradeDirection]:
        direction = TradeDirection.TRADE_DIRECTION_UNSPECIFIED
        count_bars_in_a_row = 0

        for c in reversed(changes):
            if c == 0:
                continue

            if direction == TradeDirection.TRADE_DIRECTION_UNSPECIFIED:
                if c > 0:
                    direction = TradeDirection.TRADE_DIRECTION_BUY
                else:
                    direction = TradeDirection.TRADE_DIRECTION_SELL
            elif (c > 0 and direction == TradeDirection.TRADE_DIRECTION_SELL) or (
                    c < 0 and direction == TradeDirection.TRADE_DIRECTION_BUY):
                break
            count_bars_in_a_row += 1
        return count_bars_in_a_row, direction


async def backtest_one_instrument(
        instrument: Instrument,
        start_cash: int,
        comm: float,
        from_: datetime,
        to: datetime,
        min_count_bars: int
) -> StrategyResult:
    candles = await CSVCandles.download_or_read(
        instrument=instrument, from_=from_, to=to,
        interval=CandleInterval.CANDLE_INTERVAL_DAY,
        delta=timedelta(days=365)
    )
    candles.check_datetime_consistency()

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(start_cash)
    cerebro.broker.setcommission(comm)

    filepath = CSVCandles.get_filepath(instrument, interval=CandleInterval.CANDLE_INTERVAL_DAY)
    data = MyCSVData(dataname=filepath, fromdate=from_, todate=to)
    cerebro.adddata(data)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addstrategy(StrategyLongTrendBreakDown, min_count_bars=min_count_bars)

    strats = cerebro.run()
    # logging.info(cerebro.broker.get_value())
    cerebro.plot(style='candlestick')

    return StrategyResult(
        instrument=instrument,
        start_cash=start_cash,
        trades=strats[0].trades,
        sharpe_ratio=strats[0].analyzers.sharpe.get_analysis()['sharperatio']
    )


async def main():
    to = DateTimeFactory.now()
    start_cash = 100_000
    comm = .0005
    min_count_bars = 8

    instrument = await get_instrument_by(id='ROSN', id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code='TQBR')
    strategy_result = await backtest_one_instrument(
        instrument=instrument,
        start_cash=start_cash,
        comm=comm,
        from_=instrument.first_1day_candle_date,
        to=to,
        min_count_bars=min_count_bars
    )
    print(strategy_result)
    exit()

    instruments = await Shares.from_IMOEX()
    strategies_results = []
    for instrument in instruments:
        strategy_result = await backtest_one_instrument(
            instrument=instrument,
            start_cash=start_cash,
            comm=comm,
            from_=instrument.first_1day_candle_date,
            to=to,
            min_count_bars=min_count_bars
        )
        strategies_results.append(strategy_result)
        logging.info(f'\n{strategy_result}\n')

    results_with_trades = [r for r in strategies_results if r.trades]
    results_sorted_by_successful_trades = sorted(results_with_trades, key=lambda x: x.pnlcomm)
    for s in results_sorted_by_successful_trades:
        print(s)
        print()

    results = StrategiesResults(results_with_trades)
    print(results)


if __name__ == '__main__':
    asyncio.run(main())
