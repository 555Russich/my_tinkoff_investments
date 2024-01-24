import sys
from pathlib import Path


DIR_PROJECT = Path(__file__).parent.parent
DIR_GLOBAL = DIR_PROJECT.parent
if DIR_GLOBAL.name != 'Trading':
    raise FileNotFoundError(f'Project must be in `Trading` directory.')
sys.path.append(str(DIR_GLOBAL.absolute()))

TOKENS_FULL_ACCESS, TOKENS_READ_ONLY, DIR_CANDLES, DIR_CANDLES_1DAY, DIR_CANDLES_1MIN = None, None, None, None, None
from config_global import TOKENS_FULL_ACCESS, TOKENS_READ_ONLY, DIR_CANDLES, DIR_CANDLES_1DAY, DIR_CANDLES_1MIN # noqa

FILEPATH_ENV = DIR_GLOBAL / '.tinkoff_tokens.env'
