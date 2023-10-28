from tinkoff.invest.schemas import Quotation, HistoricCandle

from src.schemas import Candle


class Converter:
    @staticmethod
    def quotation_to_decimal(value: Quotation) -> float:
        return value.units + value.nano * 10 ** -9

    @staticmethod
    def decimal_to_quotation(value: float) -> Quotation:
        units, nano = [x for x in str(value).split('.')]
        return Quotation(int(units), int(nano * 10 ** 9))

    @staticmethod
    def candle(candle: HistoricCandle) -> Candle:
        return Candle(
            Converter.quotation_to_decimal(candle.open),
            Converter.quotation_to_decimal(candle.high),
            Converter.quotation_to_decimal(candle.low),
            Converter.quotation_to_decimal(candle.close),
            candle.volume,
            candle.time,
            candle.is_complete
        )
