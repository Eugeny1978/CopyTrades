from time import sleep
import pandas as pd
import ccxt                                                 # Объекты DataFrame
from connectors.bitteam import BitTeam
from connectors.data_base import DataBaseRequests
from connectors.logic_errors import LogicErrors

PAUSE = 1 # Пауза между Запросами
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT', 'LINK/USDT')
ORDER_COLUMNS = ('symbol', 'type', 'side', 'price', 'amount')
div_line = '-----------------------------------------------------------------------------------------------------'

class Exchanges:
    """
    1. Соединение с Биржами
    2. Создать Подключение к Аккаунту Патрона
    3. Создать Подключения к Аккаунтам Клиентов

    4. Получить Лимитные Ордера Аккаунта (Таблицу Агрегированную по Price + (Buy Sell))
    5. Сравнить Агрегированные Ордера Патрона с Клиентом

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
    # Способ подключения к бирже используя getattr
    # id = 'binance'
    # exchange = getattr(ccxt, id)()
    # print(exchange.has)

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

    def get_account_orders(self, exchange):
        orders = []
        for symbol in SYMBOLS:
            order_list = exchange.fetch_open_orders(symbol)
            for order in order_list:
                orders.append(order)
        return self.convert_orders_to_df(orders)
        # Получается глубокий список (список в с писке)
        # order_list = [self.patron_exchange.fetch_open_orders(symbol) for symbol in SYMBOLS]
        # orders = [order for order in order_list]
        # return orders

    def convert_orders_to_df(self, orders):
        # ('symbol', 'type', 'side', 'price', 'amount')
        df = pd.DataFrame(columns=ORDER_COLUMNS)
        for order in orders:
            # для BitTeam - другие Столбцы
            df.loc[len(df)] = [order['symbol'], order['type'], order['side'], order['price'], order['remaining']]
        return df.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()

    def get_patron_ordertable(self):
        self.patron_orders = self.get_account_orders(self.patron_exchange)
        return self.patron_orders

    def get_ordertables_for_copy_clients(self, patron_orders):
        ordertables_for_copy_clients = {}
        for client_name, client_exchange in self.client_exchanges.items():
            index = 0
            template_orders = patron_orders.copy()
            template_orders['amount'] = template_orders['amount'] * self.data_base.clients['rate'][index]

            client_orders = self.get_account_orders(client_exchange)
            client_orders['amount'] = -client_orders['amount']
            table_for_copy = pd.concat([template_orders, client_orders])
            agg_table_for_copy = table_for_copy.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()
            ordertables_for_copy_clients[client_name] = agg_table_for_copy
            print(agg_table_for_copy)
            index += 1
        return ordertables_for_copy_clients

    def copy_orders(self, ordertables_for_copy_clients):

        for exchange_name, table in ordertables_for_copy_clients.items():
            account_db_index = 0
            if not len(table):
                account_db_index += 1
                continue # пустая таблица - ничего корректировать не надо
            for index, order in table.iterrows():
                client_exchange = self.client_exchanges[exchange_name]
                if order['amount'] > 0: # не хватает - выставляю ордер
                    order_amount = order['amount']
                else: # отрицательн значение - необходимо урезать.
                    # Предварительно сниму все ордера по этому символу с этой ценой
                    self.cancel_orders_with_price(client_exchange, order['symbol'], order['side'], order['price'])
                    # Выставлю одним ордером Полный объем ориентируясь на таблицу ордеров патрона.
                    # account_rate = self.get_account_rate('')
                    order_amount = self.get_amount_price_patron_orders(order['symbol'], order['side'], order['price'], account_db_index) # прописать полный объем по данной цене
                if order_amount: # если есть объем по данной цене и side
                    client_exchange.create_order(symbol=order['symbol'], type='limit', side=order['side'], price=order['price'], amount=order_amount)
            account_db_index += 1

    def get_orders_with_price(self, client_exchange, symbol, side, price):
        """
        Только Лимитные Ордера
        """
        all_orders = client_exchange.fetch_open_orders(symbol)
        price_orders = []
        for order in all_orders:
            if order['side'] == side and order['price'] == price and order['type'] == 'limit':
                temp_order = {'id': order['id'], 'side': order['side'], 'price': order['price']}
                price_orders.append(temp_order)
        return price_orders

    def cancel_orders_with_price(self, client_exchange, symbol, side, price):
        price_orders = self.get_orders_with_price(client_exchange, symbol, side, price)
        print(f'Биржа: {client_exchange}. | Будут Отменены Ордера "{side.upper()}" для Цены: {price}:', *price_orders, sep='\n')
        for order in price_orders:
            client_exchange.cancel_order(order['id'], symbol)

    def get_amount_price_patron_orders(self, symbol, side, price, account_db_index):
        patron = self.patron_orders
        account_rate = self.data_base.clients['rate'][account_db_index]
        filter = f"symbol == '{symbol}' and type == 'limit' and side == '{side}' and price == {price}"
        row_order = patron.query(filter)
        if len(row_order):
            amount = patron.query(filter)['amount'][0] * account_rate
        else:
            amount = 0
        return amount

    def get_balance(self, exchange):
        balance = exchange.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        if exchange == BitTeam:
            df = df.astype(float)
        df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
        return df_compact