import json
from pathlib import Path
from dataclasses import dataclass

from dotenv import dotenv_values


DIR_PROJECT = Path(__file__).parent
DIR_DATA = DIR_PROJECT / 'data'
DIR_CSV = DIR_DATA / 'csv'
DIR_JSON = DIR_DATA / 'json'
DIR_JSON_INSTRUMENTS = DIR_JSON / 'instruments'
DIR_CSV_INSTRUMENTS = DIR_CSV / 'instruments'
DIR_CSV_1DAY = DIR_CSV_INSTRUMENTS / '1day'
DIR_CSV_1MIN = DIR_CSV_INSTRUMENTS / '1min'

FILEPATH_ENV = Path('.tinkoff_tokens.env')
FILEPATH_LOGGER = Path('trading.log')


@dataclass
class Config:
    TOKENS_FULL_ACCESS: list[str]
    TOKENS_READ_ONLY: list[str]


config_values = dotenv_values(FILEPATH_ENV)
cfg = Config(
    TOKENS_FULL_ACCESS=json.loads(config_values.get('TOKENS_FULL_ACCESS', '[]')),
    TOKENS_READ_ONLY=json.loads(config_values.get('TOKENS_READ_ONLY', '[]')),
)

for dir_ in (
        DIR_DATA,
        DIR_CSV,
        DIR_CSV_INSTRUMENTS,
        DIR_CSV_1DAY,
        DIR_CSV_1MIN,
        DIR_JSON
):
    dir_.mkdir(exist_ok=True)
