from time import sleep
import pandas as pd
import ccxt                                                 # Объекты DataFrame
from connectors.bitteam import BitTeam
from connectors.data_base import DataBaseRequests
from connectors.logic_errors import LogicErrors

PAUSE = 1 # Пауза между Запросами

class Exchanges:
    """
    1. Соединение с Биржами
    2. Создать Подключение к Аккаунту Патрона
    3. Создать Подключения к Аккаунтам Клиентов

    2. Получить Лимитные Ордера Патрона (Таблицу Агрегированную по Price + (Buy Sell))
    3. Получить Лимитные Ордера Клиентов (Таблицу Агрегированную по Price + (Buy Sell))
    Сравнить Таблицу Ордера
    """

    def __init__(self):
        self.data_base = DataBaseRequests()
        self.patron_exchange = self.__connect_patron()
        self.client_exchanges = self.__connect_clients()

    connects = {
        'BitTeam': BitTeam,
        'Binance': ccxt.binance,
        'Mexc': ccxt.mexc,
        'ByBit': ccxt.bybit
    }

    def __connect_exchange(self, name_exchange, keys={}):
        connect = self.connects[name_exchange](keys)
        if not isinstance(connect, BitTeam):
            connect.load_markets()
        return connect

    def __connect_patron(self):
        name_exchange = self.data_base.patron['exchange'][0]
        keys = {'apiKey': self.data_base.patron['apiKey'][0], 'secret': self.data_base.patron['secret'][0]}
        return self.__connect_exchange(name_exchange, keys)

    def __connect_clients(self):
        client_connects = {}
        for index, client in self.data_base.clients.iterrows():
            name_exchange = client['exchange']
            keys = {'apiKey': client['apiKey'], 'secret': client['secret']}
            client_connects[client['name']] = self.__connect_exchange(name_exchange, keys)
            sleep(PAUSE)
        return client_connects


    def get_patron_orders(self):














    def get_balance(self):
        balance = self.exchange.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        if self.data_base.exchange == 'BitTeam':
            df = df.astype(float)
        df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
        return df_compact