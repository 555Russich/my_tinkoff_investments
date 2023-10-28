import asyncio
import logging
from datetime import datetime, timedelta

from tinkoff.invest import (
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


from src.my_logging import log_and_exit
from src.token_manager import token_controller


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
