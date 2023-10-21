from datetime import datetime, timezone, timedelta

from tinkoff.invest.schemas import Quotation, HistoricCandle
from tinkoff.invest.utils import now

from src.schemas import MyHistoricCandle


class Converter:
    @staticmethod
    def quotation_to_decimal(value: Quotation) -> float:
        return value.units + value.nano * 10 ** -9

    @staticmethod
    def decimal_to_quotation(value: float) -> Quotation:
        units, nano = [x for x in str(value).split('.')]
        return Quotation(int(units), int(nano * 10 ** 9))

    @staticmethod
    def candle(candle: HistoricCandle) -> MyHistoricCandle:
        return MyHistoricCandle(
            Converter.quotation_to_decimal(candle.open),
            Converter.quotation_to_decimal(candle.high),
            Converter.quotation_to_decimal(candle.low),
            Converter.quotation_to_decimal(candle.close),
            candle.volume,
            candle.time,
            candle.is_complete
        )

    @staticmethod
    def str2dt(dt: str) -> datetime:
        return datetime.strptime(dt, '%d.%m.%y').replace(tzinfo=timezone.utc)

    @staticmethod
    def input_daterange(
            look_days_back: int = None,
            from_: str = None,
            to: str = None
    ) -> tuple[datetime, datetime]:
        if look_days_back:
            to = now()
            return to - timedelta(days=look_days_back), to
        return Converter.str2dt(from_), Converter.str2dt(to)
