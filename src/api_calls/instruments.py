from datetime import datetime

from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest import (
    Instrument,
    Share,
    Currency,
    Bond,
    Future,
    Dividend,
    InstrumentIdType,
)

from src.token_manager import token_controller


@token_controller()
async def get_shares(client: AsyncServices = None) -> list[Share]:
    return (await client.instruments.shares()).instruments


@token_controller(single_response=True)
async def get_instrument_by(
        id: str,
        id_type: InstrumentIdType,
        class_code: str = None,
        client: AsyncServices = None
) -> Instrument:
    if id_type == InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER:
        assert class_code
    return (await client.instruments.get_instrument_by(id_type=id_type, id=id)).instrument


@token_controller()
async def get_dividends(figi: str, from_: datetime, to: datetime, client: AsyncServices = None) -> list[Dividend]:
    return (await client.instruments.get_dividends(figi=figi, from_=from_, to=to)).dividends
