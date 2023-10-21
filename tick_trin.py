import json
import os
import time
from datetime import datetime, timedelta

from tinkoff.invest import Client, RequestError

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import dash
import plotly

import api_tokens
from nasdaq_api import get_tickers_nasdaq100
from export import get_tickers_by_index
from MOEX_main import get_index_composition, change_axis_range, get_all_rus_shares

INDEX = 'all_ru'
CURRENT_TOKEN = 't.X30a7xz0vKUsyKU8Jjj-cO0uDwbhn5b-HXbm7qsnr5Xgdui28pU0KR_mxpaL-njVe2UT1wXsMq3H542mms55oA'


def run():
    # start_tick_and_trin_1_window(INDEX)
    plotly_tick_and_trin()


def sleep_reset_limits():
    sleep_time = 60 - datetime.utcnow().second + 2
    print(f'Sleeping for {sleep_time} seconds to reset limits\n' + '-' * 100)
    time.sleep(sleep_time)


def calculate_money(money_value):
    return money_value.units + money_value.nano * 10 ** -9


def get_figis_by_tickers(tickers: list, filename_shares='jsons/updates/shares.json'):
    with open(filename_shares) as f:
        shares = json.load(f)
    return [{'ticker': ticker, 'figi': share['figi']} for ticker in tickers for share in shares if
            ticker == share['ticker']]


def get_candles_by_figi(client, figi, days_back=7, candle_interval=5):
    """
    :param client: connection with Tinkoff
    :param figi: instrument "id"
    :param days_back:
    :param candle_interval: 1_MIN = 1, 5M = 2, 15M = 3, 1H = 4, 1D = 5
    :return:
    """
    c = client.market_data.get_candles(figi=figi,
                                       from_=datetime.utcnow() - timedelta(days=days_back),
                                       to=datetime.utcnow(),
                                       interval=candle_interval)
    return c.candles


def get_previous_candle_by_candles(candles):
    if not candles:
        candle = []
    elif candles[-1].is_complete is False and len(candles) == 1:
        candle = []
    elif candles[-1].is_complete:
        candle = candles[-1]
    else:
        candle = candles[-2]
    return candle


def get_last_candle(candles):
    if not candles:
        candle = []
    else:
        candle = candles[-1]
    return candle


def get_last_price_and_volume(token, figi):
    with Client(token) as client:
        c = client.market_data.get_candles(figi=figi,
                                           from_=datetime.utcnow() - timedelta(days=1),
                                           to=datetime.utcnow(),
                                           interval=5)
        if not c.candles: return []
        return {'close_price': calculate_money(c.candles[-1].close), 'date': c.candles[-1].time.strftime('%d.%m.%y'),
                'volume': c.candles[-1].volume}


def save_previous_close_prices_json(index: str):
    path_file, move = check_or_create_or_edit(index)
    tickers = choose_function_to_get_tickers(index)
    tickers_figis = get_figis_by_tickers(tickers)
    check_in_tinkoff(tickers, tickers_figis)

    if move is False: return path_file

    d = get_previous_close_prices(tickers_figis)

    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=4)

    # if move is True: sleep_reset_limits()

    return path_file


def check_or_create_or_edit(index: str):
    path_folder = f'jsons/close_prices'
    path_file = f'{path_folder}/{index}.json'

    if f'{index}.json' in os.listdir(path_folder):
        with open(path_file, encoding='utf-8') as f:
            try:
                j = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f'File "{path_file}" is repairing')
                return path_file, True

        if type(j) == dict: return path_file, True

        dates = [d['date'] for d in j]
        most_repeated_date = max(set(dates), key=dates.count)
        tickers_different_date = [{d['ticker']: d['date']} for d in j if d['date'] != most_repeated_date]
        if tickers_different_date: print(f'{tickers_different_date} with different date in "{path_file}"')

        if (datetime.utcnow() - timedelta(days=1)).strftime('%d.%m.%y') == most_repeated_date:
            move = False
            print(f'File "{path_file}" is fine')
        else:
            print(f'File "{path_file}" is changing')
            move = True
    else:
        print(f'File "{path_file}" is creating')
        move = True

    return path_file, move


def choose_function_to_get_tickers(index: str):
    if index in ['IMOEX', 'MOEXFN', 'MOEXCH']:
        tickers = get_index_composition(index)
    elif index == 'all_ru':
        tickers = get_all_rus_shares()
    elif index == 'ndx':
        try:
            tickers = get_tickers_nasdaq100()
        except TypeError:
            tickers = get_tickers_by_index(index)
    else:
        tickers = get_tickers_by_index(index)
    return tickers


def check_in_tinkoff(tickers: list, tickers_figis: list):
    tickers_in_tinkoff = [d['ticker'] for d in tickers_figis]
    not_in_tinkoff = list(set(tickers) - set(tickers_in_tinkoff))
    if not_in_tinkoff: print(f'{len(not_in_tinkoff)}/{len(tickers)} not in tinkoff')
    return not_in_tinkoff


def get_previous_close_prices(tickers_figis: list, new_data=None, none_close_prices=None):
    global CURRENT_TOKEN

    if new_data is None:
        new_data = []
    if none_close_prices is None:
        none_close_prices = []

    with Client(CURRENT_TOKEN) as client:
        for d in tickers_figis[len(new_data):]:
            try:
                candles = get_candles_by_figi(client=client, figi=d['figi'])
                candle = get_previous_candle_by_candles(candles)
            except RequestError as e:
                if e.code.RESOURCE_EXHAUSTED:
                    CURRENT_TOKEN = api_tokens.change_token(CURRENT_TOKEN)
                    new_data = get_previous_close_prices(tickers_figis, new_data, none_close_prices)
                    return new_data

            if candle:
                d['close_price'] = calculate_money(candle.close)
                d['date'] = candle.time.strftime('%d.%m.%y')
                new_data.append(d)
            else:
                none_close_prices.append(d['ticker'])

            if new_data[-1]['figi'] == tickers_figis[-1]['figi']:
                if none_close_prices: print(
                    f"Can't get close price for last 7 days for these companies: {none_close_prices}")
                return new_data


def read_figis_and_close_prices(path):
    with open(path) as f:
        j = json.load(f)
    return [{'ticker': d['ticker'], 'figi': d['figi'], 'close_price': d['close_price']} for d in j]


def get_last_prices_and_volumes(figis_prices: list, new_data=None, none_last_prices=None):
    global CURRENT_TOKEN

    if new_data is None:
        new_data = []
    if none_last_prices is None:
        none_last_prices = []

    with Client(CURRENT_TOKEN) as client:
        for d in figis_prices[len(new_data):]:

            try:
                candles = get_candles_by_figi(client, d['figi'], days_back=1)
                candle = get_last_candle(candles)
            except RequestError as e:
                if e.code.RESOURCE_EXHAUSTED:
                    CURRENT_TOKEN = api_tokens.change_token(CURRENT_TOKEN)
                    new_data = get_last_prices_and_volumes(figis_prices, new_data, none_last_prices)
                    return new_data

            if candle:
                d['last_price'] = calculate_money(candle.close)
                d['volume'] = candle.volume
                new_data.append(d)
            else:
                none_last_prices.append(d['ticker'])

            if new_data[-1]['figi'] == figis_prices[-1]['figi']:
                if none_last_prices:
                    print(f"Can't get last prices for: {none_last_prices}")
                return new_data


def calculate_tick(figis_prices: list):
    tick = 0
    for d in figis_prices:
        if d['last_price'] - d['close_price'] > 0:
            tick += 1
        elif d['last_price'] - d['close_price'] < 0:
            tick -= 1
        else:
            pass

    return {'count': len(figis_prices), 'tick': tick}


def calculate_trin(figis_prices: list):
    n_up = 0
    n_down = 0
    v_up = 0
    v_down = 0

    for d in figis_prices:
        if d['last_price'] - d['close_price'] > 0:
            n_up += 1
            v_up += d['volume']
        elif d['last_price'] - d['close_price'] < 0:
            n_down += 1
            v_down += d['volume']
        else:
            pass

    try:
        trin = round((n_up / n_down) / (v_up / v_down), 2)
    except ZeroDivisionError:
        print("TRIN can't be calculated. Probably exchange closed\n" + '-' * 100)
        trin = 0
    # print(f'trin={trin}, n_up={n_up}, n_down={n_down}, v_up={v_up}, v_down={v_down}')
    return {f'count': len(figis_prices), 'trin': trin}


def get_interval(figis_prices):
    n_tokens = len(api_tokens.read_txt_tokens())
    return 60 / (1 / ((len(figis_prices)) / (300 * n_tokens)))


def start_tick_and_trin_1_window(index: str):
    path = save_previous_close_prices_json(index)
    figis_prices = read_figis_and_close_prices(path)

    interval = get_interval(figis_prices)
    # interval = 2
    print(f'Interval: {interval} seconds')

    def get_tick_and_trin():
        figis_prices_volumes = get_last_prices_and_volumes(figis_prices)
        tick = calculate_tick(figis_prices_volumes)
        trin = calculate_trin(figis_prices_volumes)
        return tick, trin

    x = []
    y_tick, y_trin = [], []
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5.9, 9))
    fig.tight_layout()

    def update_tick_and_trin(abrakadabra):
        tick, trin = get_tick_and_trin()

        x.append(datetime.now().strftime('%H:%M:%S'))
        y_tick.append(int(tick['tick']))
        y_trin.append(trin['trin'])

        ax1.clear()
        ax2.clear()

        ax1.plot(x, y_tick)
        ax2.plot(x, y_trin)

        ax1.yaxis.tick_right()
        ax2.yaxis.tick_right()

        ax1.set_title(f'TICK: {index} ; Value: {tick["tick"]}/{tick["count"]}')
        ax2.set_title(f'TRIN: {index} ; Value: {trin["trin"]}')

        ax1.set_xticks(change_axis_range(x, 4))
        ax2.set_xticks(change_axis_range(x, 4))

        ax1.set_ylim(min(y_tick) - 2, max(y_tick) + 2)
        ax2.set_ylim(min(y_trin) - 0.05, max(y_trin) + 0.05)
        # ax1.autoscale()
        # ax2.autoscale()

        ax1.grid(True)
        ax2.grid(True)

    ani = animation.FuncAnimation(fig, update_tick_and_trin, interval=interval * 1000)
    plt.show()


def plotly_tick_and_trin():
    app = dash.Dash(__name__)
    app.layout = dash.html.Div([
        dash.html.H4('H4 title?!'),
        dash.html.Div(id='live-update-text'),
        dash.dcc.Graph(id='live-update-graph'),
        dash.dcc.Interval(
            id='interval-component',
            interval=3 * 1000,
            n_intervals=0
        )
    ])

    # @app.callback(dash.dependencies.Output('live-update-text', 'children'),
    #               dash.dependencies.Input('interval-component', 'n_intervals'))
    # def update_metrics(n):

    @app.callback(dash.dependencies.Output('live-update-text', 'figure'),
                  dash.dependencies.Input('interval-component', 'n_intervals'))
    def update_graph_live(n):
        

def main():
    run()


if __name__ == '__main__':
    main()
