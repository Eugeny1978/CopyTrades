from time import sleep
from random import uniform
from connectors.exchanges_mexc import Exchanges
from connectors.logic_errors import LogicErrors
from data_base.path_to_base import DATABASE
import sqlite3 as sq
import json
import ccxt

PAUSE = 1           # Пауза между Запросами
ACCOUNT_PAUSE = 2   # Пауза между Обработкой Клиентов
SYMBOLS = ('DEL/USDT', )  # Сравнение по Торгуемым Парам
div_line =    '-' * 120
DT_TABLE = 'Patrons_Mexc'



def jprint(data):
    print(json.dumps(data), div_line, sep='\n')

def get_apikeys():
    with sq.connect(DATABASE) as connect:
        connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
        curs = connect.cursor()
        curs.execute(f"SELECT name, exchange, apiKey, secret, password FROM {DT_TABLE} WHERE status LIKE 'Active'")
        responce = curs.fetchone()
        if not responce:
            raise LogicErrors('База Данных: Не найден Аккаунт-ПАТРОН')
        apikeys = dict(apiKey=responce['apiKey'], secret=responce['secret'])
        return apikeys


def main():

    patron = ccxt.mexc(get_apikeys())
    trades = patron.fetch_my_trades(symbol=SYMBOLS[0])
    jprint(trades)


if __name__ == "__main__":
    main()