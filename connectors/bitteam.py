import requests                                 # Библиотека для создания и обработки запросов
import sqlite3 as sq                            # Библиотека  Работа с БД
from typing import Literal                      # Создание Классов Перечислений
from data_base.path_to_base import DATABASE    # Путь к БД (хранение/запись Доступных Торгуемых Пар и их значений)

# Допустимый Формат Написания Торговых Пар (Символов)
# symbol='del_usdt' - родной
# symbol='DEL/USDT' - Унификация с ccxt. Преобразуется в del_usdt

OrderSide = Literal['buy', 'sell']
OrderType = Literal['limit', 'market']
UserOrderTypes = Literal['history', 'active', 'closed', 'cancelled', 'all'] # history = closed + cancelled

class BitTeam(): # Request
    base_url = 'https://bit.team/trade/api'
    status = None           # Статус-код последнего запроса 200 - если ок
    data = None             # Данные последнего запроса
    database = DATABASE
    auth = None
    __name__ = 'BitTeam'

    def __str__(self):
        return self.__name__

    def __init__(self, account={'apiKey': None, 'secret': None}):
        self.account = account

    @staticmethod
    def format_symbol(symbol: str):
        """
        Привожу Унифицированный Формат к Родному
        """
        return symbol.lower().replace('/', '_')

    def __request(self, path:str, method:str='get', params={}, data={}):
        """
        # Если понадобится прописать Заголовок headers = {'user-agent': 'my-app/0.0.1'} добавлю
        :path: Локальный Путь к Конечной Точке
        :method: 'get', 'post'
        :params: payloads = {} Параметры (дополняют url ? &)
        :data: body = {} Тело Запроса
        :return: Возвращает Данные Запроса
        """
        url = (self.base_url + path)

        match method:
            case 'get':
                response = requests.get(url, auth=self.auth, params=params, data=data)
            case 'post':
                response = requests.post(url, auth=self.auth, params=params, data=data)
            case _:
                response = {}
        self.status = response.status_code
        self.data = response.json() # json.dumps(response)

        match self.status: # Проверка Прохождения Запроса
            case 200:
                if self.data['ok'] and 'result' in self.data:
                    return self.data
            case _:
                print(f'Статус-Код: {self.status} | {self.data}')
                raise('Запрос НЕ Прошел!')

    def fetch_order_book(self, symbol='del_usdt'):
        """
        Стакан Цен по выбранной Паре
        Также Стакан есть и в запросе "pair". Но там он обрезан лимитом в 50 слотов
        """
        symbol = self.format_symbol(symbol)
        return self.__request(path=f'/orderbooks/{symbol}')

    def fetch_ticker(self, symbol='del_usdt'):
        """
        Весь Стакан есть и в запросе "orderbooks". Здесь он обрезан лимитом в 50 слотов
        # Мин. шаг размера Лота. Кол-во знаков в Дроби после целой части. int()
        print(f"Шаг Размера Лота: {self.date['result']['pair']['baseStep']}")
        # Кол-во знаков в Дроби после целой части. str()
        print(f"ЦЕНА. Кол-во Знаков после целой части: {self.date['result']['pair']['settings']['price_view_min']}")
        # Кол-во знаков в Дроби после целой части. str()
        print(f"Размер Позы. Кол-во Знаков после целой части: {self.date['result']['pair']['settings']['lot_size_view_min']}")
        # Мин. размер Лота относительно Доллара US. str()
        print(f"Мин. Размер Позы в USD: {self.date['result']['pair']['settings']['limit_usd']}")
        """
        symbol = self.format_symbol(symbol)
        return self.__request(path=f'/pair/{symbol}')

    def info_symbols(self):
        """
        Получения информации обо всех торговых парах
        """
        self.__request(path='/pairs')
        self.__load_symbols_database() # Возможно сделать доп проверку чтобы не постоянно скидывать в базу
        return self.data

    def __load_symbols_database(self): # Применять ТОЛЬКО сразу после Метода info_symbols
        """
        Получает данные по Всем Парам и записывает их в базу Данных SQL.
        id, name, baseStep, quoteStep
        Перед записью существующие записи удаляет.
        """
        with sq.connect(self.database) as connect:
            curs = connect.cursor()
            curs.execute("""
            CREATE TABLE IF NOT EXISTS Symbols
            (id INTEGER PRIMARY KEY, name TEXT, baseStep INTEGER, quoteStep INTEGER)""")
            curs.execute("""DELETE FROM Symbols""")
            for s in self.data['result']['pairs']:
                curs.execute("""
                INSERT INTO Symbols (id, name, baseStep, quoteStep) 
                VALUES (:Id, :Name, :BaseStep, :QuoteStep)""",
                {'Id': s['id'], 'Name': s['name'], 'BaseStep': s['baseStep'], 'QuoteStep': s['quoteStep']})


# --- ПРИВАТНЫЕ ЗАПРОСЫ. Требуется Предварительная Авторизация -----------------------------

    def authorization(self):
        if (not self.account['apiKey']) or (not self.account['secret']):
            print('Ошибка Авторизации. Задайте/Проверьте Публичный и Секретный АПИ Ключи')
            raise
        basic_auth = requests.auth.HTTPBasicAuth(self.account['apiKey'], self.account['secret'])
        self.auth = basic_auth

    def fetch_balance(self):
        """
        Полный Баланс По Спот Аккаунту
        """
        if not self.auth: self.authorization()
        return self.__request(path=f'/ccxt/balance')['result']

    def __get_pairId_database(self, symbol):
        with sq.connect(self.database) as connect:
            curs = connect.cursor()
            curs.execute(f"SELECT id FROM Symbols WHERE name LIKE '{symbol}'")
            return str(curs.fetchone()[0])

    def create_order(self, symbol: str, type: OrderType, side: OrderSide, amount: float, price: float=0):
        """
        Привести к Виду:
        body = {'pairId':   str, #  '24' del_usdt
                'side':     str, # "buy", "sell"
                'type':     str, # "limit", "market"
                'amount':   str, # '330' (value in coin1 (farms))
                'price':    str  # '0.04' (price in base coin (usdt))
                }
        """
        if not self.auth: self.authorization()
        pairId = self.__get_pairId_database(self.format_symbol(symbol))
        body = {'pairId': pairId,
                'side': side,
                'type': type,
                'amount': str(round(amount, 6)) # пока округляю до 6 знаков
                }
        if type == 'limit':
            body['price'] = str(round(price, 6)) # пока округляю до 6 знаков
        return self.__request(path='/ccxt/ordercreate', method='post', data=body)

    def cancel_order(self, id: (int, str)):
        """
        cancel_order(self, id: str, symbol: Optional[str] = None, params={}) # ccxt
        id_order = data['result']['id'] # create_order(body)
        """
        if not self.auth: self.authorization()
        body = {"id": id}
        return self.__request(path='/ccxt/cancelorder', method='post', data=body)

    def cancel_all_orders(self, symbol=None):
        """
        cancel_all_orders(self, symbol: Optional[str] = None, params={}) # ccxt
        pairId 1-100 - по конкретной паре || 0 - all pairs | 24 - del_usdt
        """
        if not self.auth: self.authorization()
        if symbol:
            pairId = self.__get_pairId_database(self.format_symbol(symbol))
        else:
            pairId = 0
        body = {"pairId": pairId}
        self.__request(path='/ccxt/cancel-all-order', method='post', data=body)
        if pairId:
            print(f'BitTeam. Удалены Все Ордера по Символу: {symbol}')
        else:
            print(f'BitTeam. Удалены ВСЕ Ордера')
        return self.data

    def fetch_order(self, order_id: (int or str)):
        """
        # fetch_order(self, id: str, symbol: Optional[str] = None, params={})  # ccxt
        Информация об Ордере по его ID
        """
        if not self.auth: self.authorization()
        return self.__request(path=f'/ccxt/order/{order_id}')

    def fetch_orders(self, symbol=None, since=None, limit=1000, type:UserOrderTypes='all', offset=0, order='', where=''):
        """
        Хринит Информацию за последние 3 суток (судя по тестам)
        fetch_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={})
        Ордера за Текущую Дату
        type= 'history', 'active', 'closed', 'cancelled', 'all'| history = closed + cancelled
        offset=х - смещение: не покажет первые Х ордеров
        {{baseUrl}}/trade/api/ccxt/ordersOfUser?limit=10&offset=0&type=active&order=<string>&where=<string>
        Для order='', where='': Из документации НЕ понятно Что за Объект должен передаваться
        Статус-Код: 400 | {'message': '"order" must be of type object', 'path': ['order'], 'type': 'object.base',
        'context': {'type': 'object', 'label': 'order', 'value': '', 'key': 'order'}}
        """
        if not self.auth: self.authorization()
        payloads = {
            'limit': limit,
            'type': type,
            'offset': offset
            }
        self.__request(path=f'/ccxt/ordersOfUser', params=payloads)
        if symbol:
            self.__filter_orders(self.format_symbol(symbol))
        return self.data

    def __filter_orders(self, symbol):
        """
        Фильтр по Конкретному SYMBOL
        """
        count = 0
        data_orders = []
        for order in self.data['result']['orders']:
            if order['pair'] == symbol:
                data_orders.append(order)
                count += 1
        self.data['result']['orders'] = data_orders
        self.data['result']['count'] = count

    def fetch_open_orders(self, symbol=None, since=None, limit=1000, offset=0):
        """
        Открытые (Активные Ордера) - для совместимости с ccxt
        Хвляется частныи случаем
        fetch_orders(self, symbol=None, since=None, limit=1000, type:UserOrderTypes='all', offset=0, order='', where='')
        type:UserOrderTypes='active'
        """
        return self.fetch_orders(symbol=symbol, since=since, limit=limit, type='active', offset=offset) #


    def fetch_my_trades(self, symbol=0, limit=10, offset=0, order=''):
        """
        Тесты показали Максимально: Сделки за Последние 3 дня (устанавливал лимит 1000)
        offset=х - смещение: не покажет первые Х сделок
        pairId=0 - все пары # 24 - del_usdt
        ccxt/tradesOfUser?limit=10&offset=0&order=<string>&pairId=<integer>
        ccxt:
        fetch_my_trades(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        """
        if not self.auth: self.authorization()
        payloads = {
            'limit': limit,
            'offset': offset
            # 'order': order Из Документации НЕ понятно Что сюда передавать
        }
        if symbol:
            payloads['pairId'] = self.__get_pairId_database(self.format_symbol(symbol))
        return self.__request(path=f'/ccxt/tradesOfUser', params=payloads)


    def fetch_ledger(self, limit=1000, offset=0): # fetch_transactions  # fetchLedger
        """
        {{baseUrl}}/trade/api/transactionsOfUser?limit=10&offset=0
        :return:
        """
        if not self.auth: self.authorization()
        payloads = {
            'limit': limit,
            'offset': offset
        }
        return self.__request(path='/transactionsOfUser', params=payloads)