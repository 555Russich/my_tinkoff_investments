import asyncio
import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
    InstrumentIdType,
    CandleInterval,
    TradeDirection
)

from config import FILEPATH_LOGGER
from src.schemas import Candle, StrategyResult
from src.my_logging import get_logger
from src.date_utils import DateTimeFactory, dtf
from src.api_calls import (
    get_instrument_by,
    get_shares
)
from src.market_data import get_or_read_candles

get_logger(FILEPATH_LOGGER)

TO = DateTimeFactory.now()
FROM = TO - timedelta(days=365*5)
MIN_CANDLES_COUNT = 300
MIN_COUNT_DAYS_IN_A_ROW = 8
logging.info(f'from: {dtf.datetime_strf(FROM)} | to: {dtf.datetime_strf(TO)}')


class StrategyLongTrendBreakDown:
    def __init__(self, candles: list[Candle], min_count_days_in_a_row: int):
        self._candles = candles
        self._min_count_days_in_a_row = min_count_days_in_a_row
        self._counter_days: int = 0
        self._direction = TradeDirection.TRADE_DIRECTION_UNSPECIFIED
        self._signal_direction = TradeDirection.TRADE_DIRECTION_UNSPECIFIED
        self._result_of_deals: list[float] = []

    def backtest(self) -> list[float]:
        for candle in self._candles:
            if self._signal_direction != TradeDirection.TRADE_DIRECTION_UNSPECIFIED:
                self.get_deal_result(candle)
                self._signal_direction = TradeDirection.TRADE_DIRECTION_UNSPECIFIED

            if candle.close - candle.open > 0:
                self.recognize_trade_signal(candle, TradeDirection.TRADE_DIRECTION_BUY)
            elif candle.close - candle.open < 0:
                self.recognize_trade_signal(candle, TradeDirection.TRADE_DIRECTION_SELL)
            else:
                continue
        return self._result_of_deals

    def recognize_trade_signal(self, candle: Candle, direction: TradeDirection) -> None:
        opposite_direction = self.get_opposite_direction(direction)

        if self._direction == TradeDirection.TRADE_DIRECTION_UNSPECIFIED:
            self._counter_days += 1
            self._direction = direction
        elif self._direction == direction:
            self._counter_days += 1
        elif self._direction == opposite_direction:
            if self._counter_days >= self._min_count_days_in_a_row:
                # logging.info(f'{direction=} | {self._counter_days=} | {dtf.datetime_strf(candle.time)}')
                self._signal_direction = direction

            self._counter_days = 1
            self._direction = direction

    def get_deal_result(self, candle: Candle) -> None:
        if self._signal_direction == TradeDirection.TRADE_DIRECTION_BUY:
            # price1 = candle.high - (candle.high - candle.low)/4
            price1 = candle.open
            price2 = candle.close
            res = price2 - price1
        elif self._signal_direction == TradeDirection.TRADE_DIRECTION_SELL:
            # price1 = candle.low + (candle.high - candle.low)/4
            price1 = candle.open
            price2 = candle.close
            res = -(price2 - price1)
        else:
            raise Exception

        percent = res / price1 * 100
        self._result_of_deals.append(percent)
        # logging.info(f'{price1=} | {price2=} | res={round(res, 2)} | percent={round(percent, 2)}%')

    @staticmethod
    def get_opposite_direction(direction: TradeDirection) -> TradeDirection:
        if direction == TradeDirection.TRADE_DIRECTION_SELL:
            return TradeDirection.TRADE_DIRECTION_BUY
        elif direction == TradeDirection.TRADE_DIRECTION_BUY:
            return TradeDirection.TRADE_DIRECTION_SELL


async def backtest_one_instrument(figi: str) -> StrategyResult:
    instrument = await get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi)
    candles = await get_or_read_candles(
        instrument=instrument,
        from_=FROM,
        to=TO,
        interval=CandleInterval.CANDLE_INTERVAL_DAY,
        delta=timedelta(days=365)
    )
    if len(candles) < MIN_CANDLES_COUNT:
        return StrategyResult()

    strategy = StrategyLongTrendBreakDown(candles=candles, min_count_days_in_a_row=MIN_COUNT_DAYS_IN_A_ROW)
    result_of_deals = strategy.backtest()
    strategy_result = StrategyResult(
        percent=sum(result_of_deals),
        count_deals=len(result_of_deals),
        count_successful_deals=len([x for x in result_of_deals if x > 0])
    )
    logging.info(f'#{instrument.ticker} | figi={instrument.figi} | result={round(strategy_result.percent, 2)}% |'
                 f' {strategy_result.count_successful_deals}/{strategy_result.count_deals} deals in profit')
    return strategy_result


async def backtest_multiple_instruments(figi_list: list[str]):
    strategy_result = StrategyResult()
    for figi in figi_list:
        single_result = await backtest_one_instrument(figi)
        strategy_result.percent += single_result.percent
        strategy_result.count_deals += single_result.count_deals
        strategy_result.count_successful_deals += single_result.count_successful_deals

    logging.info(f'Tested {len(figi_list)} instruments\n{strategy_result}')


async def main():
    instruments_to_backtest = [s.figi for s in await get_shares()
                               if s.first_1day_candle_date != DateTimeFactory.BUG_1DAY_CANDLE_DATE]
    # instruments_to_backtest = []
    # shares = await get_shares()
    # for share in shares:
    #     if share.ticker in ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CBOM', 'CHMF', 'ENPG', 'FEES', 'FIVE', 'GAZP', 'GLTR', 'GMKN', 'HYDR', 'IRAO', 'LKOH', 'MAGN', 'MGNT', 'MOEX', 'MTSS', 'NLMK', 'NVTK', 'OZON', 'PHOR', 'PIKK', 'PLZL', 'POLY', 'POSI', 'QIWI', 'ROSN', 'RTKM', 'RUAL', 'SBER', 'SBERP', 'SELG', 'SGZH', 'SNGS', 'SNGSP', 'TATN', 'TATNP', 'TCSG', 'TRNFP', 'UPRO', 'VKCO', 'VTBR', 'YNDX']:
    #         if share.ticker not in ['VKCO'] or share.first_1day_candle_date != DateTimeFactory.BUG_1DAY_CANDLE_DATE:
    #             instruments_to_backtest.append(share.figi)

    await backtest_multiple_instruments(instruments_to_backtest)
    # await backtest_one_instrument('BBG009GSYN76')


if __name__ == '__main__':
    asyncio.run(main())
