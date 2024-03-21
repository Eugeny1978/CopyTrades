import sqlite3 as sq                    # Работа с Базой Данных
import ccxt
import pandas as pd
import json
from time import sleep, localtime, strftime, time
from data_base.path_to_base import DATABASE
from connectors.logic_errors import LogicErrors

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30 # Макс Кол-во Отображаемых Cтрок
div_line = '------------------------------------------------------------------------------------------------------------------------------'

PATRON_NAME = 'Constantin_ByBit'
PATRON_TABLE = 'Patrons'
SYMBOLS = ('ATOM/USDT', 'BTC/USDT', 'ETH/USDT')
AMOUNT_USDT = 11
DELTA_BUY_1 = 3 # проценты отклонения от текущей цены (вниз)
DELTA_BUY_2 = 5 # проценты отклонения от текущей цены (вниз)
DELTA_BUY_3 = 7 # проценты отклонения от текущей цены (вниз)

def get_patron():
    with sq.connect(DATABASE) as connect:
        connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
        curs = connect.cursor()
        curs.execute(f"SELECT exchange, apiKey, secret, password FROM {PATRON_TABLE} WHERE name LIKE '{PATRON_NAME}'")
        responce = curs.fetchone()
        if not responce:
            raise LogicErrors('База Данных: Не найден Аккаунт-ПАТРОН')
        keys = {'apiKey': responce['apiKey'],
                'secret': responce['secret'],
                'password': responce['password']}
        patron = {'exchange': responce['exchange'],
                  'keys': keys}
        return patron

connects = {
    'ByBit': ccxt.bybit,
    'BitTeam': ccxt.bitteam,
    'Gate_io': ccxt.gateio,
    'Mexc': ccxt.mexc,
    'Okx': ccxt.okx
}

def get_step(args: list):
    decimals = []
    for value in args:
        value_str = str(value)
        if '.' in value_str:
            decimals.append(len(value_str.split('.')[1]))
        else:
            decimals.append(0)
    max_decimal = max(decimals)
    return max_decimal

def get_high_low_7days_symbol(exchange, symbol):
    ohlcv_7days = exchange.fetch_ohlcv(symbol, '1d', limit=8)
    highs, lows = [], []
    for prices in ohlcv_7days:
        highs.append(prices[2])
        lows.append(prices[3])
    max_high = max(highs)
    min_low = min(lows)
    return (max_high, min_low)

def get_advise_prices(exchange):
    columns = ['symbol', 'open24h', 'high24h', 'low24h', 'average24h', 'last', 'high7d', 'low7d', 'deltaBuy1', 'deltaBuy2', 'deltaBuy3']
    prices = pd.DataFrame(columns=columns)
    for symbol in SYMBOLS:
        ticker = exchange.fetch_ticker(symbol)
        ohlcv7d = get_high_low_7days_symbol(exchange, symbol)
        # print(json.dumps(ticker))
        ticker_prices = [ticker['open'], ticker['high'], ticker['low'], ticker['average'], ticker['last']]
        price_step = get_step(ticker_prices)
        prices.loc[len(prices)] = [
            symbol,
            *ticker_prices,
            *ohlcv7d,
            round(ticker['last']*(1 - 0.01*DELTA_BUY_1), price_step),
            round(ticker['last'] * (1 - 0.01*DELTA_BUY_2), price_step),
            round(ticker['last'] * (1 - 0.01 * DELTA_BUY_3), price_step)
        ]
    return prices

def convert_orders_to_df(orders):
    df = pd.DataFrame(columns=('symbol', 'type', 'side', 'price', 'amount'))
    for order in orders:
        df.loc[len(df)] = (order['symbol'], order['type'], order['side'], order['price'], order['remaining'])
    return df.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()

def get_temp_orders(exchange):
    orders = []
    for symbol in SYMBOLS:
        try:
            order_list = exchange.fetch_open_orders(symbol)
            for order in order_list:
                orders.append(order)
        except:
            print(f'API Биржи: Не удалось Получить список Ордеров. | Биржа: {exchange}.')
    return convert_orders_to_df(orders)

def cancel_old_orders(exchange):
    for symbol in SYMBOLS:
        exchange.cancel_all_orders(symbol)

def create_manual_orders(exchange):
    pass
    # ATOM = 'ATOM/USDT'
    # exchange.create_order(symbol=ATOM, type='limit', side='buy', amount=0, patron=0)
    # exchange.create_order(symbol=ATOM, type='limit', side='buy', amount=0, patron=0)
    # sleep(1)

    # BTC = 'BTC/USDT'
    # exchange.create_order(symbol=BTC, type='limit', side='buy', amount=0, patron=0)
    # exchange.create_order(symbol=BTC, type='limit', side='buy', amount=0, patron=0)
    # sleep(1)

    # ETH = 'ETH/USDT'
    # exchange.create_order(symbol=ETH, type='limit', side='buy', amount=0, patron=0)
    # exchange.create_order(symbol=ETH, type='limit', side='buy', amount=0, patron=0)
    # sleep(1)

if __name__ == '__main__':

    patron = get_patron()
    exchange = connects[patron['exchange']](patron['keys'])

    temp_orders = get_temp_orders(exchange)
    print('Текущие ОРДЕРА', temp_orders, div_line, sep='\n')

    advise_prices = get_advise_prices(exchange)
    print('Рекомендуемые Цены', advise_prices, div_line, sep='\n')

    # cancel_old_orders(exchange)

    # create_manual_orders(exchange)
