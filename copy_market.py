import json
import pandas as pd             # Работа с DataFrame
import sqlite3 as sq            # Работа с Базой Данных
from data_base.path_to_base import DATABASE, TEST_DB # Путь к Базе Данных
import ccxt
from datetime import datetime, timedelta, date # Работа с Временем
import pytz
from time import mktime

div_line = '-' * 120
SYMBOLS_liquid = ('ATOM/USDT', 'BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'TRX/USDT')
SYMBOLS_shit = ('DEL/USDT')
PATRON_liquid = 'Constantin_ByBit'
PATRON_shit = 'Constantin_Mexc'
DATABASE = TEST_DB
TRADE_TYPE = 'Liquid_coins'
DELTA_MIN = 3* 60 # Интервал, вглубь которого проверяется наличие новых Сделок

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

    # def get_info_text(self, symbol, amount):
    #     return f"{self.client['name']} | {self.client['exchange']} | {symbol}, Объем: {amount} | "
    #
    # def sell_market(self, symbol, amount):
    #     text = self.get_info_text(symbol, amount)
    #     try:
    #         self.connection.create_market_sell_order(symbol=symbol, amount=amount)
    #         print(text, 'ПРОДАНО по РЫНКУ')
    #     except:
    #         print(text, 'НЕ Удалось Продать по Рынку')
    #
    # def buy_market(self, symbol, amount):
    #     text = self.get_info_text(symbol, amount)
    #     try:
    #         self.connection.create_market_buy_order(symbol=symbol, amount=amount)
    #         print(text, 'КУПЛЕНО по РЫНКУ')
    #     except:
    #         print(text, 'НЕ Удалось Купить по Рынку')

    def market_order(self, symbol: str, amount: float, side: str):
        order_side = {'sell': self.connection.create_market_sell_order,
                      'buy': self.connection.create_market_buy_order}
        info = {'sell': "ПРОДАЖА '---' ",
                'buy': "ПОКУПКА '+++' "}
        text = f"{self.client['name']} | {self.client['exchange']} | {symbol}, Объем: {amount} | "
        try:
            order_side[side](symbol=symbol, amount=amount)
            print(text, f"{info[side]} ПО РЫНКУ")
        except:
            print(text, f"НЕ Удалась {info[side]} по рынку!")


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

    def record_id_trade(self, trade: dict):
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"""INSERT INTO MarketTrades (symbol, id, side, amount, cost, price, datetime) VALUES 
            ('{trade['symbol']}', '{trade['id']}', '{trade['side']}', {trade['amount']}, {trade['cost']}, {trade['price']}, '{trade['datetime']}')""")

    def get_new_trades(self):
        start_dt = str(datetime.now(tz=pytz.UTC) - timedelta(minutes=DELTA_MIN))
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
                                trade_info = {'symbol': symbol,
                                              'id': trade['id'],
                                              'side': trade['side'],
                                              'amount': trade['amount'],
                                              'cost': round(trade['cost'], 1),
                                              'price': trade['price'],
                                              'datetime': trade['datetime']}
                                new_trades.append(trade_info)
                                self.record_id_trade(trade_info)
            except:
                print(f"По каким-то причинам Запрос не был Обработан Биржей")
        if len(new_trades):
            print(f"За последние {DELTA_MIN} мин. Есть НОВЫЕ (необработанные) Сделки ПО РЫНКУ:")
        return new_trades

    def get_price_amount_for_trade(self, symbol, cost_usdt):
        price = self.connection.fetch_ticker(symbol)['last']
        amount = float(self.connection.amount_to_precision(symbol, (cost_usdt / price)))
        return (price, amount)



if __name__ == '__main__':

    # БЛОК: КАКИЕ COINs НЕОБХОДИМО продать ПО РЫНКУ. Смотрю свежие Сделки ПО РЫНКУ Патрона
    patron = PatronData(TRADE_TYPE)

    # # БЛОК Предварительно Куплю и Продам для Тестов
    # symbol_s, cost_usdt_s = 'ATOM/USDT', 10
    # symbol_b, cost_usdt_b = 'ETH/USDT', 10
    # price_s, amount_s = patron.get_price_amount_for_trade(symbol_s, cost_usdt_s)
    # price_b, amount_b = patron.get_price_amount_for_trade(symbol_b, cost_usdt_b)
    # print(f"{symbol_s = } | {price_s = } | {amount_s = }")  ###
    # print(f"{symbol_b = } | {price_b = } | {amount_b = }")  ###
    # sell_trade = patron.connection.create_market_sell_order(symbol=symbol_s, amount=amount_s)
    # buy_trade = patron.connection.create_market_buy_order(symbol=symbol_b, amount=amount_b)
    # print(json.dumps(buy_trade)) # проверил сделка проходит. Дает инфу только buy_trade['id']. Остальные Поля = Null
    # print(json.dumps(sell_trade)) # проверил сделка проходит. Дает инфу только sell_trade['id']. Остальные Поля = Null

    new_deals = patron.get_new_trades()
    print(*new_deals, sep='\n')

    # Клиенты
    clients = ClientData(trade='Liquid_coins').clients

    # Обход Клиентов
    for client in clients:

        trader = Trader(client) # Подготовка к Торговле
        if not trader.connection:
            continue
        print(trader.client['name'], trader.balance, div_line, sep='\n') ###

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
                        trader.market_order(symbol=symbol, amount=amount_coin, side='sell')
                case 'buy': # Покупка ПО РЫНКУ
                    trader.market_order(symbol=symbol, amount=(deal['amount'] * trader.client['rate']), side='buy')
            print(coin, table, sep='\n')
