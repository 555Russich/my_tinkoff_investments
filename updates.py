# from main import Hola
from tinkoff.invest import Client, RequestError
# from api_tokens import read_txt_tokens
from src.token_manager import TokenManager
from src.converter import Converter

import json
import datetime

PATH = '/media/russich555/hdd/Programming/Trading/data/json/updates'


def run(TOKEN):
    try:
        with Client(TOKEN) as client:
            Updates(client).update_shares()
            Updates(client).update_currencies()
            Updates(client).update_bonds()
    except RequestError as e:
        print(str(e))


class Updates:
    def __init__(self, client):
        self.client = client

    def update_shares(self):
        shares = self.client.instruments.shares().instruments
        if len(shares) < 1:
            raise Exception("Error with getting shares list")

        l = [
            {
                'figi': share.figi,
                'ticker': share.ticker,
                'sector': share.sector,
                'lot': share.lot,
                'currency': share.currency,
                'class_code': share.class_code,
                'exchange': share.exchange,
                'country_of_risk': share.country_of_risk,
                'ipo_date': share.ipo_date.strftime('%d.%m.%Y'),
                'nominal': Converter.quotation_to_decimal(share.nominal),
                'trading_status': share.trading_status,
            }
            for share in shares]
        with open(f"{PATH}/shares.json", "w", encoding='utf-8') as f:
            f.write(json.dumps(l, indent=4))

        return l

    def update_currencies(self):
        currencies = self.client.instruments.currencies().instruments
        if len(currencies) < 1:
            raise Exception("Error with getting currencies list")

        l = [
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

        with open(f"{PATH}/currencies.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(l, ensure_ascii=False, indent=4))

        return l

    def update_bonds(self):
        bonds = self.client.instruments.bonds().instruments
        if len(bonds) < 1:
            raise Exception("Error with getting bonds list")

        l = [
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

        with open(f"{PATH}/bonds.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(l, ensure_ascii=False, indent=4))

        return l


if __name__ == '__main__':
    tokens = [d['token'] for d in TokenManager.read_json()]
    for i, t in enumerate(tokens):
        run(t)
        print(f'{i+1}/{len(tokens)} updated')
