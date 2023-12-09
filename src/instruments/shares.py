from typing import Self
from collections import UserList

from tinkoff.invest import InstrumentIdType
from moex_api import MOEX
from src.api_calls.instruments import get_instrument_by


class Shares(UserList):
    @classmethod
    async def from_IMOEX(cls) -> Self:
        async with MOEX() as moex:
            tickers = await moex.get_index_composition('IMOEX')
        return await cls.get_by_tickers(tickers)

    @classmethod
    async def from_TQBR(cls) -> Self:
        async with MOEX() as moex:
            tickers = await moex.get_TQBR_tickers()
            print(tickers)
        return await cls.get_by_tickers(tickers)

    @classmethod
    async def get_by_tickers(cls, tickers: list[str]) -> Self:
        return cls([await get_instrument_by(t, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code='TQBR')
                    for t in tickers])
