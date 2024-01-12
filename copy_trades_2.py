from time import sleep                  # Паузы
import pandas as pd                     # Объекты DataFrame
import numpy as np                      # Использую для округления всех зщначений в колонке ДатаФрейма
import ccxt                             # Библиотека для АПИ Запросов к Биржам
from connectors.data_base import DataBaseRequests   # Первичные Данные из Базы Данных
from connectors.logic_errors import LogicErrors     # Обработка Логических Ошибок (Исключений)

PAUSE = 1           # Пауза между Запросами
ACCOUNT_PAUSE = 5   # Пауза между Обработкой Клиентов
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')  # Сравнение по Торгуемым Парам
ORDER_COLUMNS = ('symbol', 'type', 'side', 'price', 'amount') # Колонки для ДатаФремов
div_line = '-----------------------------------------------------------------------------------------------------'

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

    def __init__(self):
        self.data_base = DataBaseRequests()
        self.patron_exchange = self.__connect_patron()
        self.client_exchanges = self.__connect_clients()
        self.symbol_decimals = self.__get_symbol_decimals()

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


    def __get_symbol_decimals(self):
        for client_exchange in self.client_exchanges.values():
            pass




def main():

    exchanges = Exchanges()
    print(exchanges.__dict__)

main()