from datetime import datetime

from tinkoff.invest import CandleInterval

from src.my_tinkoff.date_utils import TZ_UTC
from src.my_tinkoff.schemas import Candle, Candles
from tests.conftest import TEST_DIR_CANDLES
from tests.schemas import InstrumentInfo, CandlesTestCase


SBER = InstrumentInfo(
    ticker='SBER',
    uid='e6123145-9665-43e0-8413-cd61b8aa9b13',
    class_code='TQBR',
    exchange='MOEX_EVENING_WEEKEND',
    first_1day_candle_date=datetime(2000, 1, 4, 7, 0, tzinfo=TZ_UTC)
)
CNTL = InstrumentInfo(
    ticker='CNTL',
    uid='c05fd0a1-0c8e-4bc3-bf9e-43e364d278ef',
    class_code='TQBR',
    exchange='MOEX'
)
POSI = InstrumentInfo(
    ticker='POSI',
    uid='de08affe-4fbd-454e-9fd1-46a81b23f870',
    class_code='TQBR',
    exchange='MOEX_EVENING_WEEKEND',
    first_1day_candle_date=datetime(2021, 12, 17, 0, 0, tzinfo=TZ_UTC)
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
CASE_POSI_GAPS_EVERYWHERE = CandlesTestCase(
    filepath=TEST_DIR_CANDLES / 'POSI_gaps_everywhere.csv',
    dt_from=datetime(year=2019, month=5, day=11, tzinfo=TZ_UTC),
    dt_to=datetime(year=2024, month=5, day=9, tzinfo=TZ_UTC),
    count_candles=584,
    dt_first_candle=datetime(2021, 12, 17, tzinfo=TZ_UTC),
    dt_last_candle=datetime(2024, 5, 8, tzinfo=TZ_UTC),
    interval=CandleInterval.CANDLE_INTERVAL_DAY
)


test_instruments = [SBER, CNTL]
dataset_candles = [
    # (SBER, CASE_SBER_FULL_RANGE_EXISTS),
    # (CNTL, CASE_CNTL_FULL_RANGE_EXISTS),
    # (CNTL, CASE_CNTL_GAP_IN_THE_BEGINNING),
    # (CNTL, CASE_CNTL_GAP_IN_THE_END),
    (POSI, CASE_POSI_GAPS_EVERYWHERE)
]

candles_math = [
    (
        Candles([
            Candle(open=285.01, high=287.74, low=277.1, close=279.95, volume=90415000, time=datetime(year=2020, month=12, day=14)),
            Candle(open=278.53, high=283.76, low=276.06, close=278.7, volume=84193000, time=datetime(year=2020, month=12, day=15)),
            Candle(open=278, high=280.84, low=276.14, close=278.35, volume=54749000, time=datetime(year=2020, month=12, day=16))
        ]),
        Candles([
            Candle(open=252, high=253.7, low=243.8, close=246.26, volume=9773000, time=datetime(year=2020, month=12, day=14)),
            Candle(open=245.88, high=248.75, low=242.74, close=245.33, volume=8568000, time=datetime(year=2020, month=12, day=15)),
            Candle(open=245.6, high=247, low=243.55, close=246.97, volume=5807000, time=datetime(year=2020, month=12, day=16))
        ]),
        [
            (
                Candles.__add__,
                Candles([
                    Candle(open=537.01, high=541.44, low=520.9000000000001, close=526.21, volume=100188000, time=datetime(2020, 12, 14, 0, 0)),
                    Candle(open=524.41, high=532.51, low=518.8, close=524.03, volume=92761000, time=datetime(2020, 12, 15, 0, 0)),
                    Candle(open=523.6, high=527.8399999999999, low=519.69, close=525.32, volume=60556000, time=datetime(2020, 12, 16, 0, 0))
                ])
            ),
        ]
    ),
    (
        Candles([
            Candle(open=123.75, high=152.89, low=115.11, close=131.12, volume=396287000, time=datetime(year=2022, month=2, day=25)),
            Candle(open=131, high=156.2, low=130.15, close=136.24, volume=159464000, time=datetime(year=2022, month=3, day=24)),
        ]),
        Candles([
            Candle(open=118.8, high=159.87, low=115, close=131.3, volume=32401000, time=datetime(year=2022, month=2, day=25)),
            Candle(open=131.3, high=131.3, low=131.3, close=131.3, volume=0, time=datetime(year=2022, month=3, day=21)),
            Candle(open=131.3, high=131.3, low=131.3, close=131.3, volume=0, time=datetime(year=2022, month=3, day=22)),
            Candle(open=131.3, high=131.3, low=131.3, close=131.3, volume=0, time=datetime(year=2022, month=3, day=23)),
            Candle(open=130, high=157.95, low=130, close=135.4, volume=18069000, time=datetime(year=2022, month=3, day=24))
        ]),

        [
            (
                Candles.__add__,
                Candles([
                    Candle(open=242.55, high=312.76, low=230.11, close=262.42, volume=428688000, time=datetime(2022, 2, 25)),
                    Candle(open=255.05, high=284.19, low=246.41, close=262.42, volume=396287000, time=datetime(year=2022, month=3, day=21)),
                    Candle(open=255.05, high=284.19, low=246.41, close=262.42, volume=396287000, time=datetime(year=2022, month=3, day=22)),
                    Candle(open=255.05, high=284.19, low=246.41, close=262.42, volume=396287000, time=datetime(year=2022, month=3, day=23)),
                    Candle(open=261, high=314.15, low=260.15, close=271.64, volume=177533000, time=datetime(year=2022, month=3, day=24))
                ])
            )
        ],
    )
]
