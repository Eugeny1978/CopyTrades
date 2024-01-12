from connectors.exchanges_old import Exchanges, SYMBOLS
import pandas as pd
import sqlite3 as sq
from time import sleep, time, localtime, strftime    # Создание технологических Пауз

from data_base.path_to_base import DATABASE

PAUSE = 60 # Пауза Между Циклами Проверки
pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

# Для Отработки Если есть Различия по Объему:
# 1. Получаю список таких ордеров (необходим id - остальное для проверки)
# 2. Удаляю Эти ордера по их ID
# 3. Выставляю Один ордер на полный Объем (для этого необходимо обратиться к Таблице Ордеров Патрона.


def get_bot_status():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT status FROM BotStatuses WHERE bot LIKE 'Copy_bot'")
        return curs.fetchone()[0]

def get_local_time():
    t = localtime()
    current_time = strftime("%H:%M:%S", t)
    return current_time

def main():

    # Получаю Первичные Данные (Патрон, Клиенты)
    if get_bot_status() == 'Run':
        exchanges = Exchanges()
        print( f'Локальное Время: {get_local_time()}',
            'Загружены Данные Аккаунтов. | Соединение с биржами установлено',
            'Сравниваем Лимитные Ордера по Парам: ', SYMBOLS, div_line, sep='\n')
    else:
        print('Процесс не был запущен. Измените статус Бота на значение "Run"')

    while get_bot_status() == 'Run':
        start_time = time()

        # Получаю Агрегированную Таблицу Ордеров Патрона
        # patron_orders = exchanges.get_account_orders(exchanges.patron_exchange)
        patron_orders = exchanges.get_patron_ordertable()
        print('Таблица Ордеров Акк. ПАТРОНА', patron_orders, div_line, sep='\n')

        # Формирую Словарь Агрегированных Таблиц Ордеров для копирования Клиентами
        ordertables_for_copy_clients = exchanges.get_ordertables_for_copy_clients(patron_orders)

        # Копирование Ордеров
        exchanges.copy_orders(ordertables_for_copy_clients)
        print(f'Цикл Копирования Выполнен за {round(time() - start_time, 3)} сек. | {get_local_time()}')

        # Пауза между проверками
        sleep(PAUSE)
        print(f'Пауза между сверкой {PAUSE} сек. | {get_local_time()}')

    print(f'Процесс Копирования Лимитных Ордеров ОСТАНОВЛЕН. | {get_local_time()}')

main()