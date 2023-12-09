import asyncio
import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
    Instrument,
    InstrumentIdType,
    CandleInterval,
    TradeDirection
)
import backtrader as bt

from config import FILEPATH_LOGGER
from src.my_logging import get_logger
from src.date_utils import DateTimeFactory, dt_form_sys, dt_form_msc
from src.api_calls.instruments import get_instrument_by
from src.csv_candles import CSVCandles
from src.backtrader.csv_data import MyCSVData

get_logger(FILEPATH_LOGGER)
TO = DateTimeFactory.now()
FROM = TO - timedelta(days=365*5)
MIN_CANDLES_COUNT = 300
MIN_COUNT_DAYS_IN_A_ROW = 8
logging.info(f'from: {dt_form_sys.datetime_strf(FROM)} | to: {dt_form_sys.datetime_strf(TO)}')


class StrategyLongTrendBreakDown(bt.Strategy):
    def __init__(self):
        self.order = None
        self.closes = self.datas[0].close
        self.opens = self.datas[0].open
        self.highs = self.datas[0].high
        self.lows = self.datas[0].low

        self.changes = self.closes > self.opens
        self.min_count_bars_in_a_row = MIN_COUNT_DAYS_IN_A_ROW

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
            self.log(f'Order canceled/margin/rejected')

        # no pending order
        self.order = None

    def notify_trade(self, trade: bt.Trade):
        if trade.isclosed:
            self.log(f'{trade.pnl=} | {trade.pnlcomm=}')

    def next(self):
        if self.order or len(self.closes) < self.min_count_bars_in_a_row:
            return

        if self.position:
            if self.position.size < 0:
                self.buy()
            elif self.position.size > 0:
                self.sell()
            self.order = None

        prev_bars = self.changes.get(ago=-1, size=self.min_count_bars_in_a_row)
        if len(set(prev_bars)) == 1:
            is_bully_trend, is_plus_change = bool(prev_bars[0]), bool(self.changes[0])
            # self.log(f'{is_bully_trend=} | {is_plus_change=}')
            if is_bully_trend is True and is_plus_change is False:
                self.order = self.sell()
            elif is_bully_trend is False and is_plus_change is True:
                self.order = self.buy()


async def main():
    instrument = await get_instrument_by(id='NVTK', id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code='TQBR')
    candles = await CSVCandles.download_or_read(
        instrument=instrument,
        from_=instrument.first_1day_candle_date,
        # from_=FROM,
        to=TO,
        interval=CandleInterval.CANDLE_INTERVAL_DAY,
        delta=timedelta(days=365)
    )
    for i in range(1, len(candles)):
        if candles[i-1].time > candles[i].time:
            raise Exception(f'{instrument.ticker=} | {candles[i-1].time=} | {candles[i].time=}')

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100_000)
    cerebro.broker.setcommission(.0005)

    filepath = CSVCandles.get_filepath(instrument, interval=CandleInterval.CANDLE_INTERVAL_DAY)
    data = MyCSVData(dataname=filepath, fromdate=FROM, todate=TO)
    cerebro.adddata(data)

    cerebro.addstrategy(StrategyLongTrendBreakDown)

    logging.info(f'Starting Portfolio Value: {cerebro.broker.get_value()}')
    cerebro.run(notidy_order=True)
    logging.info(f'Final Portfolio Value: {cerebro.broker.get_value()}')
    # cerebro.plot(style='candlestick')


if __name__ == '__main__':
    asyncio.run(main())
