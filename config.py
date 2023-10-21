import json
from pathlib import Path
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import dotenv_values


DIR_PROJECT = Path(__file__).parent
DIR_DATA = Path(DIR_PROJECT, 'data')
DIR_CSV = Path(DIR_DATA, 'csv')
DIR_JSON = Path(DIR_DATA, 'json')
DIR_CSV_INSTRUMENTS = Path(DIR_CSV, 'instruments')
DIR_CSV_SHARES = Path(DIR_CSV_INSTRUMENTS, 'shares')

FILEPATH_ENV = Path('.env')
FILEPATH_LOGGER = Path('trading.log')

TZ = ZoneInfo('Europe/Moscow')


@dataclass
class Config:
    TOKEN_TRADE: str
    TOKENS_READ: list[str]
    TOKENS_FULL_ACCESS: list[str]


config_values = dotenv_values(FILEPATH_ENV)
cfg = Config(
    TOKEN_TRADE=config_values.get('TOKEN_TRADE'),
    TOKENS_READ=json.loads(config_values.get('TOKENS_READ', '[]')),
    TOKENS_FULL_ACCESS=json.loads(config_values.get('TOKENS_FULL_ACCESS', '[]'))
)

for dir_ in (
        DIR_DATA,
        DIR_CSV,
        DIR_CSV_INSTRUMENTS,
        DIR_CSV_SHARES,
        DIR_JSON
):
    dir_.mkdir(exist_ok=True)
