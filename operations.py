from main import Hola

import pandas as pd
pd.set_option('display.max_rows', 10000)
import datetime

from tinkoff.invest.token import TOKEN
from tinkoff.invest import Client, RequestError,  Operation, MarketDataRequest

ACC_NAME = 'Брокерский счёт'


def run():
    try:
        with Client(TOKEN) as client:
            # Operations(client).report()
            Operations(client).get_my_currency_average()
    except RequestError as e:
        print(str(e))


class Operations(Hola):

    def report(self):
        df = self.operations_by_acc(ACC_NAME)
        balance = {}
        for i, row in df.iterrows():
            if row['type'] == 'Завод денежных средств':
                balance[row['date']] = row['payment']

        for i, row in df.iterrows():
            if row['type'] == 'Вывод денежных средств':
                for k, v in balance.copy().items():
                    if row['date'] > k:
                        balance[row['date']] = v - row['payment']
        print(df)
        df_usd = df[(df['currency'] == 'usd') | ((df['figi'] == 'BBG0013HGFT4') & df['type'] == 'Удержание комиссии за операцию')]
        print(df_usd)

    def operations_by_acc(self, ACC_NAME: str):
        accs_n_names = {acc.name: acc.id for acc in self.client.users.get_accounts().accounts}
        acc_id = accs_n_names[ACC_NAME]
        df = self.get_operations_df(acc_id)
        return df

    def get_operations_df(self, account_id: str):
        r = self.client.operations.get_operations(
            account_id=account_id,
            from_=datetime.datetime(1971, 1, 1),
            to=datetime.datetime.utcnow()
        )
        if len(r.operations) < 1: return None
        df = pd.DataFrame([self.operation_to_dict(p, account_id) for p in r.operations[::-1]])

        return df

    def operation_to_dict(self, o: Operation, account_id: str):
        r = {
            'acc': account_id,
            'date': o.date,
            'type': o.type,
            'otype': o.operation_type,
            'currency': o.currency,
            'instrument_type': o.instrument_type,
            'figi': o.figi,
            'quantity': o.quantity,
            'state': o.state,
            'payment': self.calculate_money(o.payment, False),
            'price': self.calculate_money(o.price, False)
        }

        return r

    def get_my_currency_average(self):
        # my_types = []
        # for i, row in df.iterrows():
        #     if row['type'] not in my_types:
        #         my_types.append(row['type'])
        #
        # print(my_types)
        # df_ = df[df['currency'] == 'usd']
        df = self.operations_by_acc(ACC_NAME)
        d = {'quantity': 0, 'average_price': 0}
        for i, row in df.iterrows():
            if row['figi'] == 'BBG0013HGFT4' and row['currency'] == 'rub':
                if row['type'] == 'Покупка ЦБ':
                    d['quantity'] += row['quantity']
                    d['average_price'] = (d['average_price'] * d['quantity'] + row['price'] * row['quantity']) / (d['quantity'] + row['quantity'])
                elif row['type'] == 'Продажа ЦБ':
                    d['quantity'] -= row['quantity']

            if row['currency'] == 'usd' and row['type'] in ['Удержание комиссии за операцию', 'Удержание комиссии за обслуживание брокерского счёта',
                    'Покупка ЦБ', 'Продажа ЦБ', 'Передача дивидендного дохода', 'Выплата дивидендов']:
                d['quantity'] += row['payment']
        print(d)


    def operations_info(self, df):
        operation_description = ['Тип операции не определён', 'Завод денежных средств', 'Удержание налога по купонам',
                                 'Вывод ЦБ', 'Доход по сделке РЕПО овернайт', 'Удержание налога',
                                 'Полное погашение облигаций', 'Продажа ЦБ с карты', 'Удержание налога по дивидендам',
                                 'Вывод денежных средств', 'Частичное погашение облигаций', 'Корректировка налога',
                                 'Удержание комиссии за обслуживание брокерского счёта',
                                 'Удержание налога за материальную выгоду',
                                 'Удержание комиссии за непокрытую позицию', 'Покупка ЦБ', 'Покупка ЦБ с карты',
                                 'Завод ЦБ', 'Продажа в результате Margin-call', 'Удержание комиссии за операцию',
                                 'Покупка в результате Margin-call', 'Выплата дивидендов', 'Продажа ЦБ',
                                 'Выплата купонов', 'Удержание комиссии SuccessFee', 'Передача дивидендного дохода',
                                 'Зачисление вариационной маржи', 'Списание вариационной маржи',
                                 'Покупка в рамках экспирации фьючерсного контракта',
                                 'Продажа в рамках экспирации фьючерсного контракта',
                                 'Комиссия за управление по счёту автоследования',
                                 'Комиссия за результат по счёту автоследования', 'Удержание налога по ставке 15%',
                                 'Удержание налога по купонам по ставке 15%',
                                 'Удержание налога по дивидендам по ставке 15%',
                                 'Удержание налога за материальную выгоду по ставке 15%',
                                 'Корректировка налога по ставке 15%',
                                 'Удержание налога за возмещение по сделкам РЕПО по ставке 15%',
                                 'Удержание налога за возмещение по сделкам РЕПО',
                                 'Удержание налога по сделкам РЕПО', 'Возврат налога по сделкам РЕПО',
                                 'Удержание налога по сделкам РЕПО по ставке 15%',
                                 'Возврат налога по сделкам РЕПО по ставке 15%', 'Выплата дивидендов на карту',
                                 'Корректировка налога по купонам']
        o_dict = {}
        for i in range(0, len(operation_description)):
            df_ = df[df['otype'] == i]
            if df_['payment'].sum() != 0:
                o_dict[operation_description[i]] = df_['payment'].sum()
        df_o_info = pd.DataFrame(o_dict, index=[0])
        return df_o_info

    def get_total_yield(self, df):
        df_zavod = df[df['type'] == 'Завод денежных средств']
        df_vyvod = df[df['type'] == 'Вывод денежных средств']

        zavod_dict = {}
        vyvod_dict = {}

        for row in df_zavod.iloc:
            zavod_dict[row['date']] = row['payment']
        for row in df_vyvod.iloc:
            vyvod_dict[row['date']] = row['payment']
        print(vyvod_dict)
        print(zavod_dict)
        balance_dict = zavod_dict.copy()
        zavod = 0
        for date in balance_dict.keys():
            balance_dict[date] = balance_dict[date] + zavod
            zavod = balance_dict[date]
        # print(balance_dict)

        for date_v in list(vyvod_dict.keys()):
            for date_b in list(balance_dict.keys()):
                if date_v < date_b:
                    # print('earlier', date_b, date_v, balance_dict[date_b])
                    continue
                else:
                    balance_dict[date_v] = balance_dict[date_b] + vyvod_dict[date_v]
                    # print('later', date_b, date_v, balance_dict[date_b])
        # print(balance_dict)


def main():
    run()


if __name__ == '__main__':
    main()