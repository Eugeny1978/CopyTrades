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
DELTA_MIN = 60 # Интервал вглуь которого проверяется наличие новых Сделок

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
        connection: ccxt.Exchange = connections[account['exchange']]() # {'options': {'defaultType': 'spot'}}
        connection.load_markets()
        # connection.options['defaultType'] = 'spot'
        # connection.enableRateLimit = True # по умолчанию уже стоит
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
        self.connection: ccxt.Exchange = connect_exchange(client)
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
            trade = self.connection.create_market_sell_order(symbol=symbol, amount=amount)
            print(f"{self.client['name']} | {self.client['exchange']} | ПРОДАНО по Рынку: {symbol}, Объем: {trade['amount']}, Цена: {trade['price']}")
        except:
            print(f"{self.client['name']} | {self.client['exchange']} | НЕ Удалось Продать по Рынку: {symbol}, Объем: {amount}")

    def buy_market(self, symbol, amount, price):
        try:
            trade = self.connection.create_market_order(symbol=symbol, amount=amount, side='buy', price=price)
            print(f"{self.client['name']} | {self.client['exchange']} | КУПЛЕНО по Рынку: {symbol}, Объем: {trade['amount']}, Цена: {trade['price']}")
        except:
            print(f"{self.client['name']} | {self.client['exchange']} | НЕ Удалось Купить по Рынку: {symbol}, Объем: {amount}")


class PatronData:
    name = 'Constantin_ByBit'
    db_table = 'Patrons'

    def __init__(self, trade: str): # 'Liquid_coins', 'Shit_coins'
        self.name, self.symbols, self.db_table = self.get_constantes(trade)
        self.patron  = self.get_patron()
        self.connection: ccxt.Exchange = connect_exchange(self.patron)

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

    def not_id_trade_db(self, id):
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"""SELECT * FROM MarketTrades WHERE id IS '{id}'""")
            responce = curs.fetchone()
            not_trade = False if responce else True
            return not_trade

    def record_id_trade(self, symbol:str, id:str):
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"""INSERT INTO MarketTrades (symbol, id) VALUES ('{symbol}', '{id}')""")

    def get_new_trades(self):
        start_dt = str(datetime.now() - timedelta(minutes=DELTA_MIN))
        # start_stamp = mktime(start_dt.timetuple()) # Нужно * 1000 чб получить время по которому сравниваем. не стоку а дату
        start_stamp = self.connection.parse8601(start_dt) # встроенный метод
        new_trades = []
        for symbol in self.symbols:
            try:
                last_trades = self.connection.fetch_my_trades(symbol=symbol, since=start_stamp)
                if len(last_trades):
                    for trade in last_trades:
                        if trade['type'] == 'market':
                            if self.not_id_trade_db(trade['id']):
                                new_trades.append({'symbol': symbol,
                                                  'id': trade['id'],
                                                  'side': trade['side'],
                                                  'amount': trade['amount'],
                                                  'cost': trade['cost']})
                                self.record_id_trade(symbol, trade['id'])
                    if len(new_trades):
                        print(f"За последние {DELTA_MIN} мин. БЫЛИ Сделки ПО РЫНКУ:")
            except:
                print(f"По каким-то причинам Запрос не был Обработан Биржей")
        return new_trades



if __name__ == '__main__':

    # БЛОК: КАКИЕ COINs НЕОБХОДИМО продать ПО РЫНКУ. Смотрю свежие Сделки ПО РЫНКУ Патрона
    patron = PatronData('Liquid_coins')
    new_deals = patron.get_new_trades()
    print(*new_deals, sep='\n')

    # Клиенты
    clients = ClientData(trade='Liquid_coins').clients

    # Обход Клиентов
    for client in clients:

        trader = Trader(client) # Подготовка к Торговле
        if not trader.connection:
            continue

        # Обход Свежих сделок
        for deal in new_deals:
            symbol = deal['symbol']
            coin = symbol.split('/')[0]
            price_usdt = trader.connection.fetch_ticker(symbol)['last'] # нужно ли каждому узнеавать или один раз
            table = pd.DataFrame(columns=('client', 'exchange', 'rate', 'amount_coin', 'cost_usdt')) # необх только для распечатки таблицы
            match deal['side']:
                case 'sell': # Продажа ПО РЫНКУ
                    amount_coin = trader.get_amount_coin(coin)
                    cost_usdt = round(price_usdt * amount_coin, 2)
                    table.loc[len(table)] = (client['name'], client['exchange'], client['rate'], amount_coin, cost_usdt)
                    if cost_usdt > 10.1:
                        trader.sell_market(symbol=symbol, amount=amount_coin)
                case 'buy': # Покупка ПО РЫНКУ
                    trader.buy_market(symbol=symbol, amount=(deal['amount'] * trader.client['rate']), price=price_usdt)
            print(coin, table, sep='\n')








# ЧЕРНОВИК
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