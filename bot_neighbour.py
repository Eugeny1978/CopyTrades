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


def main():
    ACCOUNT = 'Luchnik_ByBit'
    SYMBOL = 'ATOM/USDT'
    bot = Bot(ACCOUNT, SYMBOL)
    print(bot.__dict__)



main()