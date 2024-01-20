from tinkoff.invest.schemas import Quotation, HistoricCandle, MoneyValue

from my_tinkoff_investments.schemas import Candle


def quotation2decimal(value: Quotation) -> float:
    return value.units + value.nano * 10 ** -9


def decimal2quotation(value: float) -> Quotation:
    units, nano = [x for x in str(value).split('.')]
    return Quotation(int(units), int(nano * 10 ** 9))


def moneyvalue2quotation(v: MoneyValue) -> Quotation:
    return Quotation(units=v.units, nano=v.nano)


def convert_candle(candle: HistoricCandle) -> Candle:
    return Candle(
        quotation2decimal(candle.open),
        quotation2decimal(candle.high),
        quotation2decimal(candle.low),
        quotation2decimal(candle.close),
        candle.volume,
        candle.time,
        candle.is_complete
    )
