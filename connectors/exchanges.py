from time import sleep                  # Паузы
import pandas as pd                     # Объекты DataFrame
import numpy as np                      # Использую для округления всех зщначений в колонке ДатаФрейма
import ccxt                             # Библиотека для АПИ Запросов к Биржам
from connectors.bitteam import BitTeam  # Библиотека для АПИ Запросов к Бирже BitTeam
from connectors.data_base import DataBaseRequests   # Первичные Данные из Базы Данных
from connectors.logic_errors import LogicErrors     # Обработка Логических Ошибок (Исключений)

PAUSE = 1           # Пауза между Запросами
ACCOUNT_PAUSE = 5   # Пауза между Обработкой Клиентов
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')  # Сравнение по Торгуемым Парам
ORDER_COLUMNS = ('symbol', 'type', 'side', 'price', 'amount') # Колонки для ДатаФремов
div_line = '-----------------------------------------------------------------------------------------------------'

class Exchanges:
    """
    1. Соединение с Биржами
    2. Создать Подключение к Аккаунту Патрона
    3. Создать Подключения к Аккаунтам Клиентов

    4. Получить Лимитные Ордера Аккаунта (Таблицу Агрегированную по Price + (Buy Sell))
    5. Сравнить Агрегированные Ордера Патрона с Клиентом
    Сравнить Таблицу Ордера

    Округление Ордеров до 4 знаков. 0.0001. При Цене BTC = 40000 это 4 доллара. Остальные меньше.
    Причина:
    Биржа Gate_io - Правила выставления для BTC ETH - довольно крупными кусками - и поэтому получится
    при более точном округлении - на каждом шаге будет корректировать эту незначительную разницу
    """

    def __init__(self):
        self.data_base = DataBaseRequests()
        self.patron_exchange = self.__connect_patron()
        self.client_exchanges = self.__connect_clients()

    connects = {
        'BitTeam': BitTeam,
        'Binance': ccxt.binance,
        'Mexc': ccxt.mexc,
        'ByBit': ccxt.bybit,
        'Okx': ccxt.okx,
        'Gate_io': ccxt.gateio
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
        keys = {'apiKey': self.data_base.patron['apiKey'][0],
                'secret': self.data_base.patron['secret'][0],
                'password': self.data_base.patron['password'][0],
                }
        try:
            exchange = self.__connect_exchange(name_exchange, keys)
        except:
            raise LogicErrors('API Биржи: Не удается подключиться к Бирже Акк. Патрона. | Проверьте АпиКлючи')
        return exchange

    def __connect_clients(self):
        client_connects = {}
        for index, client in self.data_base.clients.iterrows():
            name_exchange = client['exchange']
            keys = {'apiKey': client['apiKey'], 'secret': client['secret'], 'password': client['password']}
            try:
                client_connects[client['name']] = self.__connect_exchange(name_exchange, keys)
            except:
                print(f"API Биржи: Не удается подключиться к Бирже Клиента. | Проверьте АпиКлючи | Акк.: {client['name']}. Биржа: {name_exchange}.")
            sleep(PAUSE)
        return client_connects

    def get_account_orders(self, exchange):
        orders = []
        for symbol in SYMBOLS:
            try:
                order_list = exchange.fetch_open_orders(symbol)
                for order in order_list:
                    orders.append(order)
            except:
                print(f'API Биржи: Не удалось Получить список Ордеров. | Биржа: {exchange}.')
        return self.convert_orders_to_df(orders)
        # Получается глубокий список (список в с писке)
        # order_list = [self.patron_exchange.fetch_open_orders(symbol) for symbol in SYMBOLS]
        # orders = [order for order in order_list]
        # return orders

    def convert_orders_to_df(self, orders):
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

            template_orders = patron_orders.copy()
            if len(patron_orders):
                client_rate = self.data_base.clients.query(f'name == "{client_name}"')['rate'].values[0]
                template_orders['amount'] = np.round(template_orders['amount'] * client_rate, decimals=4)

            client_orders = self.get_account_orders(client_exchange)
            if len(client_orders):
                client_orders['amount'] = -client_orders['amount']
                if len(patron_orders):
                    table_for_copy = pd.concat([template_orders, client_orders])
                    agg_table_for_copy = table_for_copy.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()
                    agg_table_for_copy = agg_table_for_copy[agg_table_for_copy['amount'] != 0]
                    ordertables_for_copy_clients[client_name] = agg_table_for_copy
                else:
                    ordertables_for_copy_clients[client_name] = client_orders
            else:
                ordertables_for_copy_clients[client_name] = template_orders
        return ordertables_for_copy_clients

    def copy_orders(self, ordertables_for_copy_clients):
        for client_name, table in ordertables_for_copy_clients.items():
            client_exchange = self.client_exchanges[client_name]
            print(div_line, f'Копирование Аккаунта: {client_name} | Биржа: {client_exchange}', sep='\n')
            if not len(table):
                print('Ордера НЕ нуждаются в Корректировке', div_line, sep='\n')
                # account_db_index += 1
                continue # пустая таблица - ничего корректировать не надо
            print(f'Таблица для Корректировки Ордеров: | Mount - разница между необходимым Объемом и Текущим', table, sep='\n')
            for index, order in table.iterrows():
                # Предварительно сниму все ордера по этому символу с этой ценой и side
                # Вариант Добавления Части - повышенный риск "мелких" Ордеров - объемом менее минимально допустимого на бирже
                self.cancel_orders_with_price(client_exchange, order['symbol'], order['side'], order['price'])
                # Выставлю одним ордером Полный объем, ориентируясь на таблицу ордеров патрона.
                order_amount = self.get_amount_price_patron_orders(order['symbol'], order['side'], order['price'], client_name)
                if order_amount:  # если есть объем по данной цене и side у Патрона
                    print(f"+++ Будет СОЗДАН Ордер {order['symbol']} {order['side'].upper()} для Цены: {order['price']} Объемом: {order_amount}:")
                    try:
                        client_exchange.create_order(symbol=order['symbol'], type='limit', side=order['side'], price=order['price'], amount=order_amount)
                    except:
                        print('!!! ОШИБКА при Попытке Создать Ордер. | Скорее всего НЕ Хватает средств на счету | Либо Биржа НЕ дает выставить Данный Объем.')
            print(div_line)
            sleep(ACCOUNT_PAUSE)

    def get_orders_with_price(self, client_exchange, symbol, side, price):
        """
        Только Лимитные Ордера
        """
        price_orders = []
        try:
            all_orders = client_exchange.fetch_open_orders(symbol)
            for order in all_orders:
                if order['side'] == side and order['price'] == price and order['type'] == 'limit':
                    temp_order = {'id': order['id'], 'side': order['side'], 'price': order['price'], 'amount': order['amount']}
                    price_orders.append(temp_order)
        except:
            print(f'API Биржи: Не удалось получить Список Текущих Ордеров. | Биржа: {client_exchange}')
        return price_orders

    def cancel_orders_with_price(self, client_exchange, symbol, side, price):
        price_orders = self.get_orders_with_price(client_exchange, symbol, side, price)
        if len(price_orders):
            print(f'--- Будут ОТМЕНЕНЫ Ордера {symbol} "{side.upper()}" для Цены: {price}:', *price_orders, sep='\n')
        for order in price_orders:
            try:
                client_exchange.cancel_order(order['id'], symbol)
            except:
                print(f'API Биржи: Не удалось Удалить Ордер по его ID. | Биржа: {client_exchange}')

    def get_amount_price_patron_orders(self, symbol, side, price, client_name):
        patron = self.patron_orders
        client_rate = self.data_base.clients.query(f'name == "{client_name}"')['rate'].values[0]
        filter = f"symbol == '{symbol}' and type == 'limit' and side == '{side}' and price == {price}"
        row_order = patron.query(filter)
        if len(row_order):
            amount = round(patron.query(filter)['amount'].values[0] * client_rate, 4) # Округляю Объем
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