import asyncio
from datetime import datetime, timedelta

from tinkoff.invest import (
    CandleInterval,
    Share,
    Dividend,
    CandleInstrument,

    MarketDataRequest,
    SubscriptionAction,
    SubscriptionInterval,

    SubscribeCandlesRequest,
    SubscribeOrderBookRequest,
    SubscribeTradesRequest,
    SubscribeInfoRequest,
    SubscribeLastPriceRequest,
    GetMySubscriptions,
)
from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.exceptions import AioRequestError
from grpc import StatusCode

from src.my_logging import log_and_exit
from src.token_manager import token_controller
from src.schemas import MyHistoricCandle
from src.converter import Converter
from src.exceptions import ResourceExhausted


@token_controller
async def get_candles(
        figi: str,
        from_: datetime,
        to: datetime,
        interval: CandleInterval = CandleInterval.CANDLE_INTERVAL_1_MIN,
        delta: timedelta = timedelta(days=1),
        client: AsyncServices = None
) -> list[MyHistoricCandle]:
    candles = []
    while True:
        to_temp = from_ + delta
        # logging.info(f'{from_} , {to_temp}, {to}')
        try:
            r = await client.market_data.get_candles(
                figi=figi, interval=interval,
                from_=from_, to=to_temp
            )
            candles += [Converter.candle(candle) for candle in r.candles]
        except AioRequestError as ex:
            if ex.code == StatusCode.RESOURCE_EXHAUSTED:
                raise ResourceExhausted(candles, (from_, to))
            else:
                log_and_exit(ex)
        except Exception as ex:
            log_and_exit(ex)

        from_ = to_temp
        if from_ >= to:
            return candles


@token_controller
async def get_shares(client: AsyncServices = None) -> list[Share]:
    return (await client.instruments.shares()).instruments


@token_controller
async def get_dividends(
        figi: str,
        from_: datetime,
        to: datetime,
        client: AsyncServices = None
) -> list[Dividend]:
    return (await client.instruments.get_dividends(figi=figi, from_=from_, to=to)).dividends


async def _request_iterator(
        subscribe_candles_request: SubscribeCandlesRequest = None,
        subscribe_order_book_request: SubscribeOrderBookRequest = None,
        subscribe_trades_request: SubscribeTradesRequest = None,
        subscribe_info_request: SubscribeInfoRequest = None,
        subscribe_last_price_request: SubscribeLastPriceRequest = None,
        get_my_subscriptions: GetMySubscriptions = None
):
    yield MarketDataRequest(
        subscribe_candles_request=subscribe_candles_request,
        subscribe_order_book_request=subscribe_order_book_request,
        subscribe_trades_request=subscribe_trades_request,
        subscribe_info_request=subscribe_info_request,
        subscribe_last_price_request=subscribe_last_price_request,
        get_my_subscriptions=get_my_subscriptions
    )

    while True:
        await asyncio.sleep(1)


@token_controller
async def trade_instrument(request_iterator, client: AsyncServices = None):
    async for marketdata in client.market_data_stream.market_data_stream(
        request_iterator
    ):
        print(marketdata)


async def test():
    await trade_instrument(
        _request_iterator(
            subscribe_candles_request=SubscribeCandlesRequest(
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=[
                    CandleInstrument(
                        figi='BBG004730N88',
                        interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE,
                    )
                ]
            )
        )
    )
    # await get_my_subscriptions()

if __name__ == '__main__':
    asyncio.run(test())