# from time import sleep                # Паузы
import pandas as pd                     # Объекты DataFrame
import sqlite3 as sq                    # Работа с Базой Данных
from time import sleep, localtime, strftime, time
from data_base.path_to_base import DATABASE
from connectors.exchanges import Exchanges

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30 # Макс Кол-во Отображаемых Cтрок

# PAUSE = 1           # Пауза между Запросами
# ACCOUNT_PAUSE = 3   # Пауза между Обработкой Клиентов
# ORDER_PAUSE = 1
PAUSE = 10*60 # Пауза между Полным циклом Проверки и Копирования Ордеров (мин)
SYMBOLS = (
    'ARB/USDT',
    'APT/USDT',
    'BTC/USDT',
    'ETH/USDT',
    'ATOM/USDT',
    'DOT/USDT',
    'XLM/USDT',
    'TRX/USDT',
    'LINK/USDT',
    'AVAX/USDT',
    'ADA/USDT',
    'OP/USDT',
    'ROSE/USDT',
    'TON/USDT')  # Сравнение по Торгуемым Парам
div_line =    '--------------------------------------------------------------------------------------------------------'
double_line = '========================================================================================================'

def get_bot_status():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT status FROM BotStatuses WHERE bot LIKE 'Copy_bot'")
        return curs.fetchone()[0]

def get_local_time():
    t = localtime()
    current_time = strftime("%H:%M:%S", t)
    return current_time

def print_d(*args):
    print(*args, div_line, sep='\n')


def main():

    exchanges = None

    # 0. Инициализация: Данные Аккаунтов из БД / Соединения с Биржей / Данные по Торгуемым Парам
    if get_bot_status() == 'Run':
        exchanges = Exchanges(SYMBOLS)
        # print(exchanges.__dict__)
        print_d(f'Процесс Копирования Ордеров ЗАПУЩЕН. | {get_local_time()}')
    else:
        print("Процесс не был запущен. Измените статус 'Copy_bot' на значение 'Run'")

    while get_bot_status() == 'Run':
        start_time = time()

        # Получаю Агрегированную Таблицу Ордеров Патрона
        patron_orders = exchanges.get_patron_ordertable()
        print('Таблица Ордеров Акк. ПАТРОНА', patron_orders, div_line, sep='\n')

        # Копирование Ордеров на Аккаунты Клиентов
        exchanges.copy_orders(patron_orders)

        # Баланс Счетов:
        balances = {}
        patron_balance = exchanges.get_balance(exchanges.patron_exchange)
        balances[exchanges.data_base.patron['name'][0]] = patron_balance
        for client, exchange in exchanges.client_exchanges.items():
            balance = exchanges.get_balance(exchange)
            balances[client] = balance
        print(div_line)
        for account, balance in balances.items():
            print(f'Баланс Акк. {account}:', balance, div_line, sep='\n')

        # Время Выполнения
        print(f'Выполнено за {round(time() - start_time, 3)} сек.')

        # Пауза между Изменениями
        pause = round(PAUSE / 60)
        print(f'Выполняется Пауза {pause} мин. | {get_local_time()}')
        sleep(PAUSE)
        print_d(f'Пауза Завершена. | {get_local_time()}', div_line)

    match isinstance(exchanges, Exchanges), get_bot_status():
        case True, 'Stop':
            for client, exchange in exchanges.client_exchanges.items():
                exchanges.cancel_account_orders(client, exchange, exchanges.symbols)
            print(f'Режим STOP. | Ордера Клиентов ОТМЕНЕНЫ. | {get_local_time()}')
        case True, 'Pause':
            print(f'Режим PAUSE. | Выставленные ранее Ордера Клиентов все еще на Бирже. | {get_local_time()}')
        case True, _:
            print(f'БОТ НЕ АКТИВЕН. | {get_local_time()}')
        case _:
            pass


main()