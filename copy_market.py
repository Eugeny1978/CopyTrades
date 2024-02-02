import json
import pandas as pd             # Работа с DataFrame
import sqlite3 as sq            # Работа с Базой Данных
from data_base.path_to_base import DATABASE # Путь к Базе Данных
import ccxt
from datetime import datetime, timedelta, date # Работа с Временем
from time import mktime

SYMBOLS_liquid = ('ATOM/USDT', 'BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'TRX/USDT')
SYMBOLS_shit = ('DEL/USDT')
PATRON_liquid = 'Constantin_ByBit'
PATRON_shit = 'Constantin_Mexc'

connections = {
    'Binance': ccxt.binance,
    'BitTeam': ccxt.bitteam,
    'ByBit': ccxt.bybit,
    'GateIo': ccxt.gateio,
    'Mexc': ccxt.mexc,
    'Okx': ccxt.okx
}

def connect_exchange(account):
    try:
        connection = connections[account['exchange']]()
        connection.apiKey = account['apiKey']
        connection.secret = account['secret']
        connection.password = account['password']
        return connection
    except:
        print(f"НЕ Удалось подключиться. Проверьте API Ключи | {account['name']} | {account['exchange']}")
        return None

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

    def __init__(self, client: sq.Row):
        self.client = client
        self.connection = connect_exchange(client)
        self.balance =  self.get_balance()

    def get_balance(self):
        if not self.connection:
            return None
        balance = self.connection.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        return df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями

    def get_amount_coin(self, coin):
        try:
            return self.balance[coin]['free']
        except:
            return 0

    def sell_market(self, symbol, amount):
        try:
            self.connection.create_market_sell_order(symbol=symbol, amount=amount)
            print(f"ПРОДАНО по Рынку: {symbol} - Объем: {amount} | {self.client['name']} | {self.client['exchange']}")
        except:
            print(f"НЕ Удалось Продать по Рынку: {symbol} - Объем: {amount} | {self.client['name']} | {self.client['exchange']}")

class PatronData:
    name = 'Constantin_ByBit'
    db_table = 'Patrons'

    def __init__(self, trade: str): # 'Liquid_coins', 'Shit_coins'
        self.name, self.symbols, self.db_table = self.get_constantes(trade)
        self.patron  = self.get_patron()
        self.connection = connect_exchange(self.patron)

    def get_constantes(self, trade: str):
        match trade:
            case 'Liquid_coins':
                name = PATRON_liquid
                symbols = SYMBOLS_liquid
                db_table = 'Patrons'
            case 'Shit_coins':
                name = PATRON_shit
                symbols = SYMBOLS_shit
                db_table = 'Patrons_Mexc'
        return name, symbols, db_table


    def get_patron(self):
        query = (f"""
         SELECT name, exchange, apiKey, secret, password 
         FROM {self.db_table} 
         WHERE name IS '{self.name}'
         """)
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(query)
            return curs.fetchone()

    def get_trades(self):
        start_dt = datetime.now() - timedelta(hours=240)
        start_stamp = mktime(start_dt.timetuple())
        my_trades = {}
        for symbol in self.symbols:
            symbol_bybit = symbol + ':USDT' # именно у ByBita в данн запросе символы необходимо в таком виде подавать
            try:
                my_trades[symbol] = self.connection.fetch_my_trades() # symbol=symbol_bybit, since=start_stamp
                # print(f"ПРОДАНО по Рынку: {symbol} - Объем: {amount} | {client['name']} | {client['exchange']}")
            except:
                pass
                # print(f"НЕ Удалось Продать по Рынку: {symbol} - Объем: {amount} | {client['name']} | {client['exchange']}")
        return my_trades # trades


if __name__ == '__main__':

    ## БЛОК Формирования КАКОЙ COIN НЕОБХОДИМО продать по рынку
    patron = PatronData('Liquid_coins')
    my_trades = patron.get_trades() # trades,
    # print(patron.__dict__)

    # orders = {}
    # for symbol in patron.symbols:
    #     orders[symbol] = patron.connection.fetch_open_orders(symbol)
    # orders = patron.connection.fetch_open_orders()
    # print(json.dumps(orders), sep='\n')

    # exchange.has['fetchMyTrades']
    print(json.dumps(my_trades))


    ## БЛОК Копирование Сделок По РЫНКУ. НЕобходимо в предыдущем Блоке сформировать coin (возможно список coins)
    # coin = 'LINK'
    # symbol = f"{coin}/USDT"
    # price_usdt = 0
    # clients = ClientData(trade='Liquid_coins').clients
    # table = pd.DataFrame(columns=('client', 'exchange', 'rate', 'amount_coin', 'cost_usdt'))
    #
    # for client in clients:
    #     trader = Trader(client)
    #     if not trader.connection:
    #         continue
    #     if not price_usdt:
    #         price_usdt = trader.connection.fetch_ticker(symbol)['last']
    #     amount_coin = trader.get_amount_coin(coin)
    #     cost_usdt = round(price_usdt * amount_coin, 2)
    #     table.loc[len(table)] = (client['name'], client['exchange'], client['rate'], amount_coin, cost_usdt)
    #     if cost_usdt > 10.5:
    #         trader.sell_market(symbol=symbol, amount=amount_coin)
    #
    # print(coin, table, sep='\n')