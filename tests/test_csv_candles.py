import pytest
from tinkoff.invest import InstrumentIdType

from my_tinkoff.csv_candles import CSVCandles
from my_tinkoff.api_calls.instruments import get_instrument_by

from tests.dataset import dataset_candles


def mock_get_filepath(filepath) -> callable:
    def _wrap(instrument, interval):
        return filepath
    return _wrap


@pytest.mark.parametrize("instrument,case", dataset_candles)
async def test_download_or_read(instrument, case):
    CSVCandles.get_filepath = mock_get_filepath(case.filepath)
    instrument = await get_instrument_by(id=instrument.uid, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID)
    candles = await CSVCandles.download_or_read(instrument=instrument, from_=case.dt_from,
                                                to=case.dt_to, interval=case.interval)
    # print(len(candles))
    # print(candles[0].time)
    # print(candles[-1].time)
    assert len(candles) == case.count_candles
    assert candles[0].time == case.dt_first_candle
    assert candles[-1].time == case.dt_last_candle
