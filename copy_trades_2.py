from time import sleep                  # Паузы
import pandas as pd                     # Объекты DataFrame
import numpy as np                      # Использую для округления всех зщначений в колонке ДатаФрейма
import ccxt                             # Библиотека для АПИ Запросов к Биржам
from connectors.data_base import DataBaseRequests   # Первичные Данные из Базы Данных
from connectors.logic_errors import LogicErrors     # Обработка Логических Ошибок (Исключений)

PAUSE = 1           # Пауза между Запросами
ACCOUNT_PAUSE = 3   # Пауза между Обработкой Клиентов
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')  # Сравнение по Торгуемым Парам
div_line =    '-------------------------------------------------------------------------------------'
double_line = '====================================================================================='

class Exchanges:
    """
    0.А При Инициализации из Базы Данных Подтягиваю Данные по Аккаунтам
    0.B Для Списка Копируемых Пар под каждую Биржу Получаю Точность Округления Цен и Объемов

    Подклю
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

    def __init__(self, symbols):
        self.data_base = DataBaseRequests()
        self.patron_exchange = self.__connect_patron()
        self.client_exchanges = self.__connect_clients()
        self.client_exchange_names = self.__get_exchange_names()
        self.symbols = symbols
        self.symbol_steps = self.__get_symbol_steps_table()

    connects = {
        'ByBit': ccxt.bybit,
        'Gate_io': ccxt.gateio,
        'Mexc': ccxt.mexc,
        'Okx': ccxt.okx
    }
    # Способ подключения к бирже используя getattr
    # id = 'binance'
    # exchange = getattr(ccxt, id)()
    # print(exchange.has)

    def __connect_exchange(self, name_exchange, keys={}):
        connect = self.connects[name_exchange](keys)
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

    def __get_exchange_names(self):
        names = [name for name in self.data_base.clients['exchange']]
        return set(names)

    def __get_symbol_steps_table(self):
        df = pd.DataFrame(columns=('exchange_name', 'symbol', 'price_step', 'volume_step'))
        exchanges = set(self.client_exchanges.values())
        for exchange in exchanges:
            for symbol in self.symbols:
                steps = self.__get_symbol_steps(exchange, symbol)
                df.loc[len(df.index)] = [exchange.name, symbol, steps['price_step'], steps['volume_step']]
        return df

    def __get_symbol_steps(self, exchange, symbol):
        ticker = exchange.fetch_ticker(symbol)
        prices = [ticker['high'], ticker['low'], ticker['open'], ticker['close'], ticker['bid'], ticker['ask']]
        volumes = [ticker['bidVolume'], ticker['askVolume'], ticker['baseVolume']]
        price_step = self.__get_decimal(prices)
        volume_step = self.__get_decimal(volumes)
        return {'price_step': price_step, 'volume_step': volume_step}

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

    def get_account_orders(self, exchange):
        orders = []
        for symbol in self.symbols:
            try:
                order_list = exchange.fetch_open_orders(symbol)
                for order in order_list:
                    orders.append(order)
            except:
                print(f'API Биржи: Не удалось Получить список Ордеров. | Биржа: {exchange}.')
        return self.__convert_orders_to_df(orders)

    def __convert_orders_to_df(self, orders):
        df = pd.DataFrame(columns=('symbol', 'type', 'side', 'price', 'amount'))
        for order in orders:
            df.loc[len(df)] = [order['symbol'], order['type'], order['side'], order['price'], order['remaining']]
        return df.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()

    def get_patron_ordertable(self):
        return self.get_account_orders(self.patron_exchange)


    def copy_orders(self, patron_orders):
        match len(patron_orders):
            case 0:
                for client, exchange in self.client_exchanges.items():
                    for symbol in self.symbols:
                        exchange.cancel_all_orders(symbol)
                    print(f'{client} | Удалены Все Ордера', div_line, sep='\n')
            case _:
                for client, exchange in self.client_exchanges.items():
                    self.copy_client_orders(client, exchange, patron_orders)


    def copy_client_orders(self, client, exchange, patron_orders):
        client_orders = self.get_account_orders(exchange)
        print(double_line, f'Таблица Ордеров Акк. {client}', client_orders, div_line, sep='\n')
        template_orders = self.get_template_orders(client, exchange, patron_orders)
        delta_orders = self.compare_orders(client_orders, template_orders)

    def get_template_orders(self, client, exchange, patron_orders):
        client_rate = self.data_base.clients.query(f'name == "{client}"')['rate'].values[0]
        template = patron_orders.copy()
        template['amount'] = template['amount'] * client_rate
        for symbol in self.symbols:
            steps = self.symbol_steps.query(f'exchange_name == "{exchange.name}" and symbol == "{symbol}"')
            price_step = steps['price_step'].values[0]
            volume_step = steps['volume_step'].values[0]
            template.loc[template['symbol'] == symbol, 'price'] = round(template['price'], price_step)
            template.loc[template['symbol'] == symbol, 'amount'] = round(template['amount'], volume_step)
        print(f'Таблица Образец:', template, div_line, sep='\n')
        return template

    def compare_orders(self, client_orders, template_orders):
        if len(client_orders):
            client_orders['amount'] = -client_orders['amount']
            delta_orders = pd.concat([client_orders, template_orders])
            agg_delta_orders = delta_orders.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()
            agg_delta_orders = agg_delta_orders[agg_delta_orders['amount'] != 0]
        else:
            agg_delta_orders = template_orders
        print('Таблица Сравнения:', agg_delta_orders, sep='\n')
        return agg_delta_orders



def main():

    # Инициализация
    exchanges = Exchanges(SYMBOLS)
    # print(exchanges.__dict__)

    # Получаю Агрегированную Таблицу Ордеров Патрона
    patron_orders = exchanges.get_patron_ordertable()
    print('Таблица Ордеров Акк. ПАТРОНА', patron_orders, div_line, sep='\n')

    # Копирование Ордеров
    exchanges.copy_orders(patron_orders)

main()