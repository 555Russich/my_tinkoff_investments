from typing import Self
from collections import UserList

from tinkoff.invest import InstrumentIdType


class Shares(UserList):
    @classmethod
    async def get_by_tickers(cls, tickers: list[str]) -> Self:
        from src.api_calls.instruments import get_instrument_by
        return cls([
            await get_instrument_by(t, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code='TQBR')
            for t in tickers
        ])
