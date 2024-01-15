# from time import sleep                  # Паузы
import pandas as pd                     # Объекты DataFrame
# import numpy as np                      # Использую для округления всех зщначений в колонке ДатаФрейма
# import ccxt                             # Библиотека для АПИ Запросов к Биржам
# from connectors.data_base import DataBaseRequests   # Первичные Данные из Базы Данных
# from connectors.logic_errors import LogicErrors     # Обработка Логических Ошибок (Исключений)
import json
from connectors.exchanges import Exchanges

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 20 # Макс Кол-во Отображаемых Cтрок

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

    # for account_name, orders in exchanges.orders.items():
    #     print(div_line, account_name, orders, sep='\n')

main()