import asyncio
import json
import logging
from pathlib import Path

from tinkoff.invest import Client, RequestError

from config import DIR_JSON_INSTRUMENTS, FILEPATH_LOGGER
from src.my_logging import get_logger
from src.token_manager import TokenManager
from src.converter import Converter
from src.api_calls import get_shares, get_instrument_by


class Instruments:
    @classmethod
    async def get_shares(cls):
        shares = await get_shares()
        shares_as_dicts = [to_json_serializable(s) for s in shares]
        print(shares_as_dicts[0])
        _write_json(DIR_JSON_INSTRUMENTS / 'shares.json', shares_as_dicts)
        return shares

    @classmethod
    def _instruments_to_json(cls) -> None:
        ...

    def get_currencies(self):
        currencies = self.client.instruments.currencies().instruments
        lst = [
            {
                'figi': currency.figi,
                'ticker': currency.ticker,
                'name': currency.name,
                'class_code': currency.class_code,
                'lot': currency.lot,
                'currency': currency.currency,
                'short_enabled_flag': currency.short_enabled_flag,
                'trading_status': currency.trading_status
            }
            for currency in currencies]

        _write_json(DIR_JSON_INSTRUMENTS / 'currencies.json', lst)
        return currencies

    def get_bonds(self):
        bonds = self.client.instruments.bonds().instruments
        lst = [
            {
                'figi': bond.figi,
                'ticker': bond.ticker,
                'name': bond.name,
                'class_code': bond.class_code,
                'lot': bond.lot,
                'currency': bond.currency,
                'short_enabled_flag': bond.short_enabled_flag,
                'trading_status': bond.trading_status,
                'exchange': bond.exchange,
                'country_of_risk': bond.country_of_risk,
            }
            for bond in bonds]
        _write_json(DIR_JSON_INSTRUMENTS / 'bonds.json', lst)
        return bonds

    def get_futures(self):
        futures = self.client.instruments.futures().instruments
        print(futures)
        ...

def _write_json(filepath: Path, data: list[dict]) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


async def main():
    await Instruments.get_shares()


if __name__ == '__main__':
    asyncio.run(main())
