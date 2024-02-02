import pandas as pd             # Работа с DataFrame
import sqlite3 as sq            # Работа с Базой Данных
from data_base.path_to_base import DATABASE # Путь к Базе Данных
import ccxt
from datetime import datetime, date # Работа с Временем


class ClientData:
    def __init__(self, trade: str): # 'Liquid_coins', 'Shit_coins'
        self.trade = trade
        self.exchanges, self.db_table = self.get_exchanges()
        self.clients = self.get_clients()

    def get_exchanges(self):
        match self.trade:
            case 'Liquid_coins':
                exchanges = ('ByBit', 'Binance', 'GateIo', 'Okx')
                table = 'Clients'
            case 'Shit_coins':
                exchanges = ('BitTeam', 'Mexc')
                table = 'Client_Mexc'
        return exchanges, table

    def get_clients(self):
        row_exchanges = '\', \''.join(self.exchanges)
        query = (f"""
         SELECT name, exchange, rate, apiKey, secret, password 
         FROM {self.db_table} 
         WHERE exchange IN ('{row_exchanges}') 
             AND status IS 'Active' 
         """)
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(query)
            return curs.fetchall()




class Trader:

    connections = {
        'Binance': ccxt.binance,
        'BitTeam': ccxt.bitteam,
        'ByBit': ccxt.bybit,
        'GateIo': ccxt.gateio,
        'Mexc': ccxt.mexc,
        'Okx': ccxt.okx
    }

    def __init__(self, client):
        self.connection = self.connect_exchange()
        self.balabce =  self.get_balance()

    def connect_exchange(self):
        try:
            connection = self.connections[client['exchange']]()
            connection.apiKey = client['apiKey']
            connection.secret = client['secret']
            connection.password = client['password']
            return connection
        except:
            print(f"НЕ Удалось подключиться. Проверьте API Ключи | {client['name']} | {client['exchange']}")
            return None

    def get_balance(self):
        if not self.connection:
            return None
        balance = self.connection.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        return df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями

if __name__ == '__main__':

    clients = ClientData(trade='Liquid_coins').clients
    for client in clients:
        # print(*client, sep=' | ')
        trader = Trader(client)
        if not trader.connection:
            continue
