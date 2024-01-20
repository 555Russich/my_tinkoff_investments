# from __future__ import annotations
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
from src.instruments.shares import Shares

from datetime import datetime
import logging

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest import (
    Instrument,
    Dividend,
    InstrumentIdType,
)
from tinkoff.invest.exceptions import AioRequestError

from src.token_manager import token_controller
from src.my_logging import log_and_exit


@token_controller()
async def get_shares(client: AsyncServices = None) -> Shares:
    # from src.instruments.shares import Shares
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
        log_and_exit(ex)


@token_controller()
async def get_dividends(figi: str, from_: datetime, to: datetime, client: AsyncServices = None) -> list[Dividend]:
    return (await client.instruments.get_dividends(figi=figi, from_=from_, to=to)).dividends
