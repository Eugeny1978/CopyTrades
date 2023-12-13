import sqlite3 as sq           # Работа с БД
from data_bases.path_to_base import DATABASE # Путь к Базе Данных

STATUS_TABLE = 'BotStatuses' # Таблица Статусов Run Stop Pause


# ACCOUNT =  'Luchnik_BitTeam' # 'Constantin_BitTeam' # 'Luchnik_Mexc'
# ORDER_TABLE = 'orders_2slabs_mexc'
# BOT_NAME = 'bot_2slabs_bitteam'

class RequestsDataBase:

    def __init__(self, account_name, bot_name='', order_table=''):
        self.account = account_name
        self.bot_name = bot_name
        self.order_table = order_table
        self.exchange = self.__get_exchange()
        self.apikeys = self.__get_apikeys()

    def __get_exchange(self):
        """
        :return Получает Имя Биржи
        """
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"SELECT exchange FROM Accounts WHERE name LIKE '{self.account}'")
            try:
                exchange_name = curs.fetchone()[0]
                return exchange_name
            except:
                print(f'В Базе Данных НЕТ данного Аккаунта: {self.account}')
                raise


    def __get_apikeys(self):
        """
        :return: Получает АПИ Ключи
        """
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(f"SELECT apiKey, secret FROM Apikeys WHERE account LIKE '{self.account}' AND name LIKE 'Info'")
            try:
                keys = curs.fetchone()
                return {'apiKey': keys['apikey'], 'secret': keys['secret']}
            except:
                print(f'У данного Аккаунта в Базе Данных НЕТ API Ключей: {self.account}')
                raise


    def write_order(self, order, name:str): # name: LevelType
        """
        Записывает Ранее Созданный Ордер в Базу Данных
        :param order: dict
        :param name: str 'carrots', 'slab'
        :return:
        """
        match self.exchange:
            case 'BitTeam':
                params = [order['id'], order['symbol'], order['type'], order['side'], order['quantity'], order['price']]
            case _:
                params = [order['id'], order['symbol'], order['type'], order['side'], order['amount'], order['price']]
        params.append(name)
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            try:
                curs.execute(f"INSERT INTO {self.order_table} VALUES(?, ?, ?, ?, ?, ?, ?)", tuple(params))
            except Exception as error:
                print(error)

    def get_id_orders(self, name=None) -> list: # name:LevelType = None
        """
        :return Получает Список ID выставленных Ордеров
        """
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            injection = f" WHERE name LIKE '{name}'" if name else ''
            curs.execute(f"SELECT id FROM {self.order_table}{injection}")
            ids = [select[0] for select in curs]
        return ids

    def delete_old_orders(self, old_ids: list):
        """
        Удаляет Неактуальные Ордера
        :param old_ids: Список неактуальных ордеров
        """
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            # ids = ','.join(map(str, id_for_delete))
            ids = '\', \''.join(old_ids)
            curs.execute(f"DELETE FROM {self.order_table} WHERE id IN ('{ids}')")
        print(f'Из БД удалены Ордера: {old_ids}')

    def get_bot_status(self):
        """
        :return: Получает Статус Бота Run(Работает) Stop(Остановлен) Pause(Пауза)
        """
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"SELECT status FROM {STATUS_TABLE} WHERE bot LIKE '{self.bot_name}'")
            return curs.fetchone()[0]
