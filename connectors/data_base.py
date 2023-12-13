import sqlite3 as sq           # Работа с БД
import pandas as pd            # Преобразование в ДатаФремы (Таблицы)
from data_base.path_to_base import DATABASE # Путь к Базе Данных

class DataBaseRequests:
    """
    Задачи:
    1. Получить Аккаунт-Патрон
    2. Получить Аккунты-Клиенты
    """
    patron_columns = ('name', 'exchange', 'apiKey', 'secret')
    client_columns = ('name', 'exchange', 'apiKey', 'secret', 'rate')

    def __init__(self):
        self.patron = self.__get_patron()
        self.clients = self.__get_clients()


    def __get_patron(self):
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(f"SELECT name, exchange, apiKey, secret FROM Patrons WHERE status LIKE 'Active'")
            responce = curs.fetchone()
            if not responce:
                raise DataBaseErrors('Не найден Аккаунт-ПАТРОН')
            patron = pd.DataFrame(columns=self.patron_columns)
            patron.loc[len(patron)] = (responce)
            return patron

    def __get_clients(self):
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(f"SELECT name, exchange, apiKey, secret, rate FROM Clients WHERE status LIKE 'Active'")
            responce = curs.fetchall()
            if not responce:
                raise DataBaseErrors('Не найдены Аккаунты-Клиенты')
            clients = pd.DataFrame(columns=self.client_columns)
            for row in responce:
                clients.loc[len(clients)] = (row)
            return clients

# -----------------------------------------------------------------------------------------------
class DataBaseErrors(Exception):

    def __init__(self, *args):
        self.message = args[0] if args else None

    def __str__(self):
        if self.message:
            return '| DataBaseError, {0} |'.format(self.message)
        else:
            return '| Ошибка класса DataBaseError |'

