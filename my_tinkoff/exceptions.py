from datetime import datetime

from my_tinkoff.schemas import Candles


class TinkoffAPIError(Exception):
    pass


class APIBug(Exception):
    pass


class IncorrectFirstCandle(APIBug):
    pass


class IncorrectDatetimeConsistency(Exception):
    pass


class RequestedCandleOutOfRange(Exception):
    def __init__(self, dt_first_available_candle: datetime):
        self.dt_first_available_candle = dt_first_available_candle
        super().__init__()


class ResourceExhausted(TinkoffAPIError):
    """ Token hit limit  """

    def __init__(self, data: Candles = None):
        self.data = data
        super().__init__()


class UnexpectedCandleInterval(Exception):
    pass


class UnexpectedInstrumentType(Exception):
    pass


class InstrumentHasChanged(Exception):
    def __int__(self, ticker: str = None, figi: str = None):
        self.ticker = ticker
        self.figi = figi


class CSVCandlesError(Exception):
    pass


class CSVCandlesNeedInsert(CSVCandlesError):
    def __init__(self, to_temp: datetime):
        self.to_temp = to_temp


class CSVCandlesNeedAppend(CSVCandlesError):
    def __init__(self, from_temp: datetime, candles: Candles):
        self.from_temp = from_temp
        self.candles = candles
