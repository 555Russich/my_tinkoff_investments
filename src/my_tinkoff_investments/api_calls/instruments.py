
from datetime import datetime
import logging

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest import (
    Instrument,
    Dividend,
    InstrumentIdType,
)
from tinkoff.invest.exceptions import AioRequestError

from my_tinkoff_investments.token_manager import token_controller
from my_tinkoff_investments.instruments.shares import Shares


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
async def get_dividends(figi: str, from_: datetime, to: datetime, client: AsyncServices = None) -> list[Dividend]:
    return (await client.instruments.get_dividends(figi=figi, from_=from_, to=to)).dividends
