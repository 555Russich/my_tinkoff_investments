from dataclasses import dataclass
from collections import UserList
from typing import Self

from trading_helpers.schemas import _Candle, _Candles
from trading_helpers.date_utils import RU_HOLIDAYS
from tinkoff.invest import Instrument, Share
from my_tinkoff.enums import ClassCode


@dataclass(frozen=True)
class Candle(_Candle):
    is_complete: bool | None = None


class Candles(_Candles):
    HOLIDAYS = RU_HOLIDAYS


class Instruments(UserList[Instrument]):
    pass


class Shares(Instruments[Share]):
    @classmethod
    async def from_board(cls, board: ClassCode) -> Self:
        from my_tinkoff.api_calls.instruments import get_shares
        return cls([s for s in await get_shares() if s.class_code == board.value])
