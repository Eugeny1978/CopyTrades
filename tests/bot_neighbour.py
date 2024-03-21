import sqlite3 as sq                                 # Работа с БД
import pandas as pd                                  # Объекты DataFrame
from typing import Literal                           # Создание Классов Перечислений
from time import sleep, time, localtime, strftime    # Создание технологических Пауз
import random                                        # Случайные значения
import seaborn as sns
from matplotlib import pyplot as plt
import json
import ccxt
from data_base.path_to_base import DATABASE             # Путь к Базе Данных
from connectors.logic_errors import LogicErrors         # Ошибки

ACCOUNT = 'Luchnik_ByBit'
SYMBOL = 'ATOM/USDT'
QUANT = 0.95 # граница для определения минимального Размера для Больших Плит
DELTA = 0.15 # минимальное расстояние (в %) между соседними Плитами

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows= 200 # Макс Кол-во Отображаемых Колонок
# pd.options.display.float_format = '{:.6f}'.format # Формат отображения Чисел float
div_line =      '-------------------------------------------------------------------------------------'
double_line =   '====================================================================================='

def print_json(data):
    print(json.dumps(data))

def print_volume_values(table_name, table, accuracy=6):
    print(f'{table_name}. VOLUMES.',
          f'Median: {round(table["volume"].median(), accuracy)}',
          f'Golden Section: {round(table["volume"].quantile(0.618), accuracy)}',
          f'0.75 Quantile: {round(table["volume"].quantile(0.75), accuracy)}',
          f'Mean: {round(table["volume"].mean(), accuracy)}',
          f'SUM: {round(table["volume"].sum(), accuracy)}',
          div_line, sep='\n')

def get_order_prices(prices, price_step, type='sell'):
    order_prices = []
    for index, price in prices.items():
        if not len(order_prices):
            order_prices.append(price)
            continue
        if len(order_prices) == 3:
            break
        if type == 'sell' and price >= order_prices[-1] * (1 + DELTA/100):
            order_prices.append(price)
        if type == 'buy' and price <= order_prices[-1] * (1 - DELTA/100):
            order_prices.append(price)
    if type == 'sell':
        order_prices = [round(price - 10**-price_step, price_step) for price in order_prices]
    elif type == 'buy':
        order_prices = [round(price + 10**-price_step, price_step) for price in order_prices]
    return order_prices





# 0.
# Соединение с Биржей
# Шаг Цен, Шаг Объемов
# Определить границу объема для определения Плиты
#

# 1. Найти Среднюю цену
#
# 3. Стакан - найти Плиту
# 4. Присоседиться Плитой
# Найти 2ю Границу
# 5. Размазать на участке
#
# Пересчет:
# Стакан - плита осталась?
# Пауза
#
# Сместилась
# Пересчет на это смещение
#
# Нет Плит?
# Вопрос

class Bot:

    connects = {
        'BitTeam': ccxt.bitteam,
        'ByBit': ccxt.bybit,
        'Gate_io': ccxt.gateio,
        'Mexc': ccxt.mexc,
        'Okx': ccxt.okx
    }

    def __init__(self, account_name, symbol):
        self.account_name = account_name
        self.symbol = symbol
        self.exchange = self.__connect_exchange()
        self.price_step, self.volume_step = self.get_symbol_steps()


    def __connect_exchange(self):
        account_data = self.get_account_data()
        exchange_name = account_data['exchange']
        keys = {'apiKey': account_data['apiKey'], 'secret': account_data['secret'], 'password': account_data['password']}
        connect = self.connects[exchange_name](keys)
        connect.load_markets()
        return connect

    def get_account_data(self):
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(f"SELECT * FROM Patrons WHERE status LIKE 'Active' and name LIKE '{self.account_name}'")
            data = curs.fetchone()
            if not data:
                raise LogicErrors('База Данных: Аккаунт Не найден.')
            return dict(data)

    def get_symbol_steps(self):
        ticker = self.exchange.fetch_ticker(self.symbol)
        prices = [ticker['high'], ticker['low'], ticker['open'], ticker['close'], ticker['bid'], ticker['ask']]
        volumes = [ticker['bidVolume'], ticker['askVolume'], ticker['baseVolume']]
        price_step = self.__get_decimal(prices)
        volume_step = self.__get_decimal(volumes)
        return (price_step, volume_step)

    def __get_decimal(self, args: list):
        decimals = []
        for value in args:
            value_str = str(value)
            if '.' in value_str:
                decimals.append(len(value_str.split('.')[1]))
            else:
                decimals.append(0)
        max_decimal = max(decimals)
        return max_decimal

    def get_asks_bids_tables(self):
        orderbook = self.exchange.fetch_order_book(self.symbol, limit=200)
        columns = ('price', 'volume')
        asks = pd.DataFrame(orderbook['asks'], columns=columns)
        bids = pd.DataFrame(orderbook['bids'], columns=columns)
        # asks_volumes = asks['volume']# asks.iloc[:, 1]
        # print_volume_values('ASKS', asks, self.volume_step)
        # print_volume_values('BIDS', bids, self.volume_step)
        return {'asks': asks, 'bids' : bids}


def main():

    # Инициализация
    bot = Bot(ACCOUNT, SYMBOL)

    # Получение Таблиц Asks, Bids
    orderbook = bot.get_asks_bids_tables()
    asks = orderbook['asks']
    bids = orderbook['bids']

    # Получение Значений для Больших Плит
    ask_slab = round(asks['volume'].quantile(QUANT), bot.volume_step)
    bid_slab = round(bids['volume'].quantile(QUANT), bot.volume_step)
    print(ask_slab, bid_slab)

    # Получение Таблиц только с крупными Объемами
    big_asks = asks.query(f'volume >= {ask_slab}')
    big_bids = bids.query(f'volume >= {bid_slab}')
    print(big_asks, div_line, sep='\n')
    print(big_bids, div_line, sep='\n')

    # Получение Цен для Лимитных Ордеров:
    sell_order_prices = get_order_prices(big_asks['price'], bot.price_step, type='sell')
    buy_order_prices = get_order_prices(big_bids['price'], bot.price_step, type='buy')
    print(sell_order_prices)
    print(buy_order_prices)





main()