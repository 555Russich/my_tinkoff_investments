import asyncio
import logging
import time
from datetime import datetime
from typing import Callable

from tinkoff.invest import AsyncClient

from my_tinkoff.exceptions import ResourceExhausted
from my_tinkoff.date_utils import DateTimeFactory, is_minute_passed
from my_tinkoff.schemas import Candles
from config import TOKENS_FULL_ACCESS, TOKENS_READ_ONLY  # noqa


class TokenManager:
    _tokens = {t: True for t in TOKENS_FULL_ACCESS + TOKENS_READ_ONLY}
    _dt: datetime | None = None

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._tokens.keys())

    @classmethod
    async def get(cls):
        assert len(cls.list_all()) > 0, f'{TOKENS_FULL_ACCESS=} | {TOKENS_READ_ONLY=}'
        token = None

        if cls._dt and is_minute_passed(cls._dt):
            cls._refresh()

        for t, is_free in cls._tokens.items():
            if is_free:
                token = t
                break

        cls._dt = DateTimeFactory.now()

        if token:
            return token
        else:
            sleep_time = 60 - int(time.strftime('%S'))
            logging.debug(f'{sleep_time} seconds sleep ZZZ... All tokens are busy')
            await asyncio.sleep(sleep_time)
            return await cls.get()

    @classmethod
    def set_busy_flag(cls, token: str) -> None:
        cls._tokens[token] = False

    @classmethod
    def _refresh(cls):
        for t in cls._tokens.keys():
            cls._tokens[t] = True


def token_controller(dummy=None, single_response: bool = False) -> Callable:
    def wrapper_1(func):
        async def wrapper_2(*args, **kwargs):
            out = []
            while True:
                t = await TokenManager.get()
                async with AsyncClient(t) as client:
                    try:
                        if single_response:
                            return await func(client=client, *args, **kwargs)
                        else:
                            return out + await func(client=client, *args, **kwargs)
                    except ResourceExhausted as e:
                        TokenManager.set_busy_flag(t)

                        if isinstance(e.data, Candles) and e.data:
                            out += e.data
                            kwargs['from_'] = e.data[-1].time
                            logging.debug(f'{kwargs['from_']=} | {kwargs['to']=}')
                    except Exception:
                        raise
        return wrapper_2

    if callable(dummy):
        wrapper_1(dummy)
    else:
        return wrapper_1
