import sqlite3 as sq
from typing import Literal
import ccxt
import pandas as pd

Coins = Literal['Liquid', 'Shit']
Sides = Literal['sell', 'buy']

# Базу Данных - УЖЕ СКОПИРОВАЛ, на сервере она новее (есть новые таблицы и клиенты)
# КОПИРОВАТЬ файлы:
# manual_market_orders # Логика
# interface # фронт все аккаунты
# pages/market_orders (всесте с папкой) # фронт аккаунт создание рыночных ордеров
# create_order_bybit.json # документация
# Обновить ccxt


def style_amount(styler):
    # styler.set_caption("SPOT Balance")
    # styler.format_index(str.upper, axis=1)
    styler.format(precision=6, thousands=" ", decimal=".")
    return styler

def style_cost(styler):
    # styler.set_caption("COST USDT Balance")
    styler.format(precision=2, thousands=" ", decimal=".")
    return styler


class Accounts:

    zero = pd.DataFrame()
    connects = {
        'Binance': ccxt.binance,
        'BitTeam': ccxt.bitteam,
        'ByBit': ccxt.bybit,
        'GateIo': ccxt.gateio,
        'Mexc': ccxt.mexc,
        'Okx': ccxt.okx
    }

    def __init__(self, database, type_coins: Coins='Liquid'):
        self.database = database
        self.type_coins = type_coins
        self.client_table, self.symbol_table, self.exchange_for_last_prices = self.__get_coin_data()
        self.data: dict = self.get_accounts()
        self.symbols: tuple = self.get_symbols()
        self.last_prices: dict = self.get_last_prices()

    def __get_coin_data(self):
        match self.type_coins:
            case 'Liquid':
                client_table = 'Clients'
                symbol_table = 'Symbols'
                exchange_for_last_prices = 'ByBit'
            case 'Shit':
                client_table = 'Clients_Mexc'
                symbol_table = 'Symbols_Mexc'
                exchange_for_last_prices = 'Mexc'
            case _:
                raise ("__get_coin_data(self) | Не корректно задан Тип КриптоВалют | Допустимо: 'Liquid', 'Shit'")
        return client_table, symbol_table, exchange_for_last_prices

    def get_accounts(self) -> dict:
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"""
                SELECT name, exchange, rate, apiKey, secret, password 
                FROM {self.client_table}
                WHERE status IS 'Active'
                ORDER BY name ASC                
                """) # LIMIT 3
                accounts = dict()
                for acc in curs:
                    accounts[acc[0]] = dict(exchange=acc[1],  rate=acc[2], apiKey=acc[3], secret=acc[4], password=acc[5])
                return accounts
        except Exception as error:
            print('get_accounts(self) | Нет Доступа к базе')
            raise(error)

    def get_symbols(self):
        try:
            with sq.connect(self.database) as connect:
                curs = connect.cursor()
                curs.execute(f"SELECT name FROM {self.symbol_table}")
                symbols = [row[0] for row in curs]
                return tuple(symbols)
        except Exception as error:
            print('get_symbols(self) | Нет Доступа к базе')
            raise(error)

    def get_last_prices(self):
        """
        'Liquid' - Использую цены ByBit
        'Shit'   - Использую цены Mexc
        """
        exchange = self.connects[self.exchange_for_last_prices]()
        last_prices = {}
        for symbol in self.symbols:
            try:
                last_prices[symbol] = exchange.fetch_ticker(symbol)['last']
            except:
                last_prices[symbol] = 0
                print(f'get_last_prices(self) | Не удалось получить Последнюю Цену по Символу: {symbol}')
        return last_prices

    def get_rate(self, account_name):
        return self.data[account_name]['rate']

    def connect_account(self, account_name) -> ccxt.Exchange:
        account = self.data[account_name]
        exchange_name = account['exchange']
        try:
            connect = self.connects[exchange_name]()
            connect.apiKey = account['apiKey']
            connect.secret = account['secret']
            connect.password = account['password']
        except:
            connect = None
            print(f"connect_account(self, account_name) | {account_name} | Не удалось соединиться с Биржей {exchange_name}" )
        return connect

    def get_balance(self, connect: ccxt.Exchange) -> pd.DataFrame:
        if not connect:
            return self.zero
        try:
            balance = connect.fetch_balance()
            indexes = ['free', 'used', 'total']
            columns = [balance['free'], balance['used'], balance['total']]
            df = pd.DataFrame(columns, index=indexes)
            df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
            return df_compact
        except:
            print(f"get_balance(self, connect) | Не удалось получить Баланс {connect}")
            return self.zero

    def __get_trade_coins(self):
        return tuple([symbol.split('/')[0] for symbol in self.symbols])

    def get_cost_balance(self, balance: pd.DataFrame) -> pd.DataFrame:
        cost_balance = balance.copy()
        if cost_balance.equals(self.zero): # равно пустому датафрейму
            return self.zero
        for coin in cost_balance.columns:
            if coin == 'USDT':
                cost_balance[coin] = round(cost_balance[coin], 2)
                continue
            if coin not in self.__get_trade_coins():
                cost_balance[coin] = [0, 0, 0] # ['- Not - ', 'Trading', 0]
                continue
            symbol = coin + '/USDT'
            cost_balance[coin] = round(cost_balance[coin] * self.last_prices[symbol], 2)
        return self.__normalize_total_cost(cost_balance)

    def get_sum_cost_balance(self, cost_balance: pd.DataFrame):
        # round(cost_balance.tail(1).sum(axis=1)['total'], 2)
        return round(cost_balance.loc['total'].sum(), 2)

    def __normalize_total_cost(self, cost_balance: pd.DataFrame):
        sum_cost = self.get_sum_cost_balance(cost_balance)
        if sum_cost:
            cost_balance.loc['total_%'] = round((100 * cost_balance.loc['total'] / sum_cost), 1)
        return cost_balance

    def get_orders(self, connect: ccxt.Exchange) -> pd.DataFrame:
        if not connect:
            return self.zero
        orders = []
        for symbol in self.symbols:
            try:
                order_list = connect.fetch_open_orders(symbol)
                for order in order_list:
                    orders.append(order)
            except:
                print(f"get_orders(self, connect) | Не удалось Получить список Ордеров. | Биржа: {connect}.")
        return self.__convert_orders_to_df(orders)

    def __convert_orders_to_df(self, orders):
        df = pd.DataFrame(columns=['symbol', 'type', 'side', 'price', 'amount', 'cost'])
        for order in orders:
            order_cost = round(order['remaining'] * self.last_prices[order['symbol']], 2)
            df.loc[len(df)] = (order['symbol'],
                               order['type'],
                               order['side'],
                               order['price'],
                               order['remaining'],
                               order_cost)
        return df.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()

    def create_market_order(self, connect: ccxt.Exchange, symbol: str, side: Sides, amount: float = 0, cost: float = 0):
        flag = True
        if not symbol:
            flag = False
            print('Не задан SYMBOL!')
        if not side:
            flag = False
            print('Не задан SIDE (sell or buy)!')
        if not amount and not cost:
            flag = False
            print('Не задан Размер Ордера!')
        if not flag: return
        if not amount: #  and cost
            amount = cost / self.last_prices[symbol] # нужно ли округлять?
        try:
            return connect.create_market_order(symbol, side, amount)
        except:
            print(f"create_market_order() | Не удалось создать Ордер")


if __name__ == '__main__':

    from data_base.path_to_base import DATABASE, TEST_DB
    from pprint import pprint
    import json

    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    div_line = '-' * 120
    def dprint(args):
        pprint(args)
        print(div_line)

    def jprint(data):
        print(json.dumps(data), div_line, sep='\n')

    DB = DATABASE
    TYPE_COINS = 'Liquid' # 'Shit'

    SYMBOL = 'ATOM/USDT' # 'DEL/USDT'
    SIDE = 'buy'
    AMOUNT = 0
    COST = 10.2

    accounts = Accounts(DB, 'Liquid')
    # dprint(accounts.symbols)
    # dprint(accounts.data)
    # dprint(accounts.last_prices)

    acc_name = 'Kubarev Mihail'
    # acc_rate = accounts.get_rate(acc_name)
    acc_connect = accounts.connect_account(acc_name)
    balance = accounts.get_balance(acc_connect)
    cost_balance = accounts.get_cost_balance(balance)
    sum_cost = accounts.get_sum_cost_balance(cost_balance)
    # orders = accounts.get_orders(acc_connect)
    # dprint(acc_rate)
    # dprint(balance)
    dprint(cost_balance)
    dprint(sum_cost)
    # dprint(orders)

    # market_order = accounts.create_market_order(connect=acc_connect, symbol=SYMBOL, side=SIDE, cost=COST)
    # dprint(market_order)
    # jprint(market_order)

    # ledger = acc_connect.fetch_ledger('USDT', limit=100)
    # jprint(ledger)
