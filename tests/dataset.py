from datetime import datetime

from my_tinkoff.date_utils import TZ_UTC
from tests.conftest import TEST_DIR_CANDLES
from tests.schemas import InstrumentInfo, CandlesTestCase


SBER = InstrumentInfo(
    ticker='SBER',
    uid='e6123145-9665-43e0-8413-cd61b8aa9b13',
    class_code='TQBR',
    exchange='MOEX_EVENING_WEEKEND'
)
CNTL = InstrumentInfo(
    ticker='CNTL',
    uid='c05fd0a1-0c8e-4bc3-bf9e-43e364d278ef',
    class_code='TQBR',
    exchange='MOEX'
)

CASE_SBER_FULL_RANGE_EXISTS = CandlesTestCase(
    filepath=TEST_DIR_CANDLES / f'SBER_full_range_exists.csv',
    dt_from=datetime(year=2024, month=2, day=19, hour=13, minute=0, tzinfo=TZ_UTC),
    dt_to=datetime(year=2024, month=2, day=22, hour=13, minute=0, tzinfo=TZ_UTC),
    count_candles=2435,
    dt_first_candle=datetime(year=2024, month=2, day=19, hour=13, tzinfo=TZ_UTC),
    dt_last_candle=datetime(year=2024, month=2, day=22, hour=12, minute=59, tzinfo=TZ_UTC)
)

CASE_CNTL_FULL_RANGE_EXISTS = CandlesTestCase(
    filepath=TEST_DIR_CANDLES / f'CNTL_full_range_exists.csv',
    dt_from=datetime(year=2024, month=2, day=19, hour=7, minute=0, tzinfo=TZ_UTC),
    dt_to=datetime(year=2024, month=2, day=22, hour=7, minute=0, tzinfo=TZ_UTC),
    count_candles=811,
    dt_first_candle=datetime(year=2024, month=2, day=19, hour=7, tzinfo=TZ_UTC),
    dt_last_candle=datetime(year=2024, month=2, day=22, hour=6, minute=59, tzinfo=TZ_UTC)
)
CASE_CNTL_GAP_IN_THE_BEGINNING = CandlesTestCase(
    filepath=TEST_DIR_CANDLES / f'CNTL_gap_in_the_beginning.csv',
    dt_from=datetime(year=2024, month=2, day=19, hour=13, minute=0, tzinfo=TZ_UTC),
    dt_to=datetime(year=2024, month=2, day=22, hour=7, minute=0, tzinfo=TZ_UTC),
    count_candles=590,
    dt_first_candle=datetime(year=2024, month=2, day=19, hour=13, minute=5, tzinfo=TZ_UTC),
    dt_last_candle=datetime(year=2024, month=2, day=22, hour=6, minute=59, tzinfo=TZ_UTC),
)
CASE_CNTL_GAP_IN_THE_END = CandlesTestCase(
    filepath=TEST_DIR_CANDLES / 'CNTL_gap_in_the_end.csv',
    dt_from=datetime(year=2024, month=2, day=19, hour=7, minute=0, tzinfo=TZ_UTC),
    dt_to=datetime(year=2024, month=2, day=19, hour=16, minute=0, tzinfo=TZ_UTC),
    count_candles=266,
    dt_first_candle=datetime(year=2024, month=2, day=19, hour=7, minute=0, tzinfo=TZ_UTC),
    dt_last_candle=datetime(year=2024, month=2, day=19, hour=15, minute=48, tzinfo=TZ_UTC),
)


test_instruments = [SBER, CNTL]
dataset_candles = [
    (SBER, CASE_SBER_FULL_RANGE_EXISTS),
    (CNTL, CASE_CNTL_FULL_RANGE_EXISTS),
    (CNTL, CASE_CNTL_GAP_IN_THE_BEGINNING),
    (CNTL, CASE_CNTL_GAP_IN_THE_END),
]
