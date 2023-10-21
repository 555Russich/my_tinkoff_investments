import asyncio
import logging
import time
from datetime import datetime, timedelta

from tinkoff.invest import AsyncClient

from config import cfg
from src.exceptions import ResourceExhausted
from src.singletone import Singleton


class TokenManager(Singleton):
    _tokens_list = cfg.TOKENS_READ + cfg.TOKENS_FULL_ACCESS
    _tokens = {t: True for t in _tokens_list}
    _dt_last_get: datetime = datetime.now()

    @classmethod
    async def get(cls):
        token = None

        if is_minute_passed(cls._dt_last_get):
            for t in cls._tokens.keys():
                if token is None:
                    token = t
                    # cls._tokens[token] = False
                else:
                    cls._tokens[t] = True
        else:
            for t, is_free in cls._tokens.items():
                if is_free:
                    token = t
                    # cls._tokens[token] = False
                    break

        cls._dt_last_get = datetime.now()

        if token:
            return token
        else:
            sleep_time = 60 - int(time.strftime('%S'))
            logging.info(f'{sleep_time} seconds sleep. All tokens are busy.')
            await asyncio.sleep(sleep_time)
            return await cls.get()

    @classmethod
    def _refresh(cls):
        for t in cls._tokens.keys():
            cls._tokens[t] = True

    def _background_refresher(self):
        while True:
            self._refresh()
            print('refreshed')
            time.sleep(60 - int(time.strftime('%S')))


def token_controller(func):
    async def wrapper(*args, **kwargs):
        out = []
        while True:
            t = await TokenManager.get()
            async with AsyncClient(t) as client:
                try:
                    return out + await func(client=client, *args, **kwargs)
                except ResourceExhausted as e:
                    out += e.data[1]
                    kwargs['from_'], kwargs['to'] = e.data[2]
                    print(f'from_={e.data[2][0]} ; to={e.data[2][1]}')
    return wrapper


def is_minute_passed(old_dt: datetime) -> bool:
    dt_now = datetime.now()
    return dt_now - old_dt > timedelta(minutes=1) or dt_now.minute != old_dt.minute
