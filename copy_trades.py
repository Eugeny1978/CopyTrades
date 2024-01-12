# from time import sleep                  # Паузы
# import pandas as pd                     # Объекты DataFrame
# import numpy as np                      # Использую для округления всех зщначений в колонке ДатаФрейма
# import ccxt                             # Библиотека для АПИ Запросов к Биржам
# from connectors.data_base import DataBaseRequests   # Первичные Данные из Базы Данных
# from connectors.logic_errors import LogicErrors     # Обработка Логических Ошибок (Исключений)
from connectors.exchanges import Exchanges

PAUSE = 1           # Пауза между Запросами
ACCOUNT_PAUSE = 3   # Пауза между Обработкой Клиентов
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')  # Сравнение по Торгуемым Парам
div_line =    '-------------------------------------------------------------------------------------'
double_line = '====================================================================================='

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