import pandas as pd
import json
import datetime

# from api_tokens import read_txt_tokens
from typing import Optional
from tinkoff.invest import Client, RequestError, AccessLevel, PortfolioResponse, PortfolioPosition, Operation, \
    OperationType
from tinkoff.invest.services import Services, InstrumentsService

TRADER_COMMISSION = 0.04 / 100
TAX = 0.13
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

tokens = read_txt_tokens()


def run():
    try:
        with Client(tokens[0]) as client:
            report_totals = Hola(client).report_totals()
            report_portfolio = Hola(client).report_portfolio()
    except RequestError as e:
        print(str(e))
    return report_totals, report_portfolio


class Hola:
    def __init__(self, client: Services):
        self.usd_rate = None
        self.client = client
        self.accounts = []

    def report_portfolio(self):
        dataframes = []
        for account_id in self.get_accounts():
            df = self.get_portfolio_df(account_id)
            if df is None: continue
            dataframes.append(df)

        df = pd.concat(dataframes, ignore_index=True)
        df = self.more_data_to_df_portfolio(df)

        return df

    def report_totals(self):
        dataframes = []
        for account_id in self.get_accounts():
            df = self.get_totals_df(account_id)
            if df is None: continue
            dataframes.append(df)

        df = pd.concat(dataframes, ignore_index=True)

        return df

    def get_accounts(self):
        """
        Получаю все аккаунты и буду использовать только те
        кот текущий токен может хотябы читать,
        остальные акк пропускаю
        :return:
        """
        r = self.client.users.get_accounts()
        for acc in r.accounts:
            if acc.access_level != AccessLevel.ACCOUNT_ACCESS_LEVEL_NO_ACCESS:
                self.accounts.append(acc.id)

        return self.accounts

    def get_portfolio_df(self, account_id: str) -> Optional[pd.DataFrame]:
        """
        Преобразую PortfolioResponse в pandas.DataFrame
        :param account_id:
        :return:
        """
        r: PortfolioResponse = self.client.operations.get_portfolio(account_id=account_id)
        if len(r.positions) < 1: return None
        df = pd.DataFrame([self.portfolio_pos_to_dict(p) for p in r.positions])

        return df

    def get_totals_df(self, account_id: str):
        r = self.client.operations.get_portfolio(account_id=account_id)
        total_dict = {
            'total_amount_shares': self.calculate_money(r.total_amount_shares),
            'total_amount_bonds': self.calculate_money(r.total_amount_bonds),
            'total_amount_etf': self.calculate_money(r.total_amount_etf),
            'total_amount_currencies': self.calculate_money(r.total_amount_currencies),
            'total_amount_futures': self.calculate_money(r.total_amount_futures),
            'expected_yield': self.calculate_money(r.expected_yield)
        }
        df = pd.DataFrame(total_dict, index=[0])
        return df

    def portfolio_pos_to_dict(self, p: PortfolioPosition):
        df = {
            'figi': p.figi,
            'instrument_type': p.instrument_type,
            'currency': p.average_position_price.currency,
            'quantity': self.calculate_money(p.quantity),
            'average_position_price': self.calculate_money(p.average_position_price),
            'expected_yield': self.calculate_money(p.expected_yield),
            'current_nkd': self.calculate_money(p.current_nkd),
            'current_price': self.calculate_money(p.current_price),
        }

        if df['currency'] == 'usd':
            # expected_yield в Quotation а там нет currency
            df['expected_yield'] *= self.get_usd_rate()

        return df

    def get_usd_rate(self):
        """ Получаю курс только, если он нужен """
        if not self.usd_rate:
            u = self.client.market_data.get_last_prices(figi=['USD000UTSTOM'])
            self.usd_rate = self.calculate_money(u.last_prices[0].price)

        return self.usd_rate

    def calculate_money(self, money_value, to_rub=True):
        i = money_value.units + money_value.nano * 10 ** -9
        if to_rub and hasattr(money_value, 'currency') and getattr(money_value, 'currency') == 'usd':
            i *= self.get_usd_rate()

        return i

    def get_share_info(self, id, id_type=1):
        """ id_type: 1 - figi , 2 - ticker"""
        return self.client.instruments.bond_by.ticker(id_type=id_type, id=id)

    def more_data_to_df_portfolio(self, df):
        df['sell_sum'] = (df['current_price'] + df['current_nkd']) * df['quantity']
        df['commission'] = df['current_price'] * df['quantity'] * TRADER_COMMISSION
        df['tax'] = df.apply(lambda row: row['expected_yield'] * TAX if row['expected_yield'] > 0 else 0, axis=1)
        df['ticker'] = self.get_needed_tickers(df['figi'], df['instrument_type'])
        df['percent_change'] = df['current_price'] / df['average_position_price'] * 100 - 100
        df['sell_now'] = df['sell_sum'] - df['commission'] - df['current_price'] * df['quantity'] * TRADER_COMMISSION - df['tax']
        df['percent_sell_now'] = (df['sell_now'] / df['quantity']) / df['average_position_price'] * 100 - 100

        columns = ['ticker',
                   'figi',
                   'instrument_type',
                   'currency',
                   'quantity',
                   'average_position_price',
                   'expected_yield',
                   'percent_change',
                   'current_price',
                   'sell_sum',
                   'commission',
                   'tax',
                   'sell_now',
                   'percent_sell_now',
                   'current_nkd']

        return df[columns]

    def get_needed_tickers(self, figis, instrument_types,
                           filename_shares='jsons/shares.json',
                           filename_currencies='jsons/currencies.json',
                           filename_bonds='jsons/bonds.json'):
        with open(filename_shares) as f:
            shares = json.load(f)
        with open(filename_currencies, encoding='utf-8') as f:
            currencies = json.load(f)
        with open(filename_bonds, encoding='utf-8') as f:
            bonds = json.load(f)
        tickers = []
        for i in range(0, len(figis)):
            if instrument_types[i] == 'share':
                for share in shares:
                    if share['figi'] == figis[i]:
                        tickers.append(share['ticker'])
            elif instrument_types[i] == 'currency':
                for currency in currencies:
                    if currency['figi'] == figis[i]:
                        tickers.append(currency['ticker'])
            elif instrument_types[i] == 'bond':
                for bond in bonds:
                    if bond['figi'] == figis[i]:
                        tickers.append(bonds['ticker'])
            else:
                raise Exception('Undefined instrument type to get his ticker')

        return tickers


def main():
    # run()
    pass


if __name__ == "__main__":
    main()
