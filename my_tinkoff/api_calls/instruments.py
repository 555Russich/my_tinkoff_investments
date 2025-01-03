from datetime import datetime
import logging

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest import (
    Instrument,
    Dividend,
    InstrumentIdType,
    TradingSchedule,
    InstrumentType,
    InstrumentShort,
    InstrumentStatus,
    Future,
)
from tinkoff.invest.exceptions import AioRequestError

from my_tinkoff.token_manager import token_controller
from my_tinkoff.schemas import Shares


@token_controller()
async def get_shares(client: AsyncServices = None) -> Shares:
    return Shares((await client.instruments.shares()).instruments)


@token_controller(single_response=True)
async def get_instrument_by(
        id: str,
        id_type: InstrumentIdType,
        class_code: str = '',
        client: AsyncServices = None
) -> Instrument:
    try:
        return (await client.instruments.get_instrument_by(id_type=id_type, id=id, class_code=class_code)).instrument
    except AioRequestError as ex:
        logging.error(f'Error while getting instrument by {id=} | {class_code=}')
        raise ex


@token_controller()
async def get_dividends(instrument_id: str, from_: datetime,
                        to: datetime, client: AsyncServices = None) -> list[Dividend]:
    return (await client.instruments.get_dividends(instrument_id=instrument_id, from_=from_, to=to)).dividends


@token_controller(single_response=True)
async def get_trading_schedules(
        exchange: str = '',
        from_: datetime | None = None,
        to: datetime | None = None,
        client: AsyncServices = None
) -> list[TradingSchedule]:
    return (await client.instruments.trading_schedules(exchange=exchange, from_=from_, to=to)).exchanges


@token_controller(single_response=True)
async def find_instrument(
        query: str,
        instrument_kind: InstrumentType | None = None,
        api_trade_available_flag: bool | None = None,
        client: AsyncServices = None
) -> list[InstrumentShort]:
    return (await client.instruments.find_instrument(query=query, instrument_kind=instrument_kind,
                                                     api_trade_available_flag=api_trade_available_flag)).instruments


@token_controller(single_response=True)
async def get_future_by(
        id: str,
        id_type: InstrumentIdType | None = None,
        class_code: str | None = None,
        client: AsyncServices = None
) -> Future:
    return (await client.instruments.future_by(id=id, id_type=id_type, class_code=class_code)).instrument


@token_controller(single_response=True)
async def get_futures(
        instrument_status: InstrumentStatus = InstrumentStatus(0),
        client: AsyncServices = None
) -> list[Future]:
    return (await client.instruments.futures(instrument_status=instrument_status)).instruments
