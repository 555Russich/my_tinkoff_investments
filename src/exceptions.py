from src.schemas import TempCandles


class TinkoffAPIError(Exception):
    pass


class APIBug(Exception):
    pass


class IncorrectFirstCandle(APIBug):
    pass


class ResourceExhausted(TinkoffAPIError):
    """ Token hit limit  """

    def __init__(self, data: TempCandles = None):
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
