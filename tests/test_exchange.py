from connectors.exchanges import Exchanges
import ccxt
import json
import pandas as pd

SYMBOL = 'ATOM/USDT'
# SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

def print_json(data):
    print(json.dumps(data))

# Получаю Первичные Данные (Патрон, Клиенты)
exchanges = Exchanges()

# Получаю Агрегированную Таблицу Ордеров Патрона
# patron_orders = exchanges.get_account_orders(exchanges.patron_exchange)
patron_orders = exchanges.get_patron_ordertable()

# Формирую Словарь Агрегированных Таблиц Ордеров для копирования Клиентами
ordertables_for_copy_clients = exchanges.get_ordertables_for_copy_clients(patron_orders)

# Для Отработки Ветки Если Минусовой Объем
# То есть у клиента суммарно на этой цене стоит Объем ордеров больше чем у Патрона
# То Действия такие
# 1. Получаю список таких ордеров (необходим id - остальное для проверки)
# 2. Удаляю Эти ордера по их ID
# 3. Выставляю Один ордер на полный Объем (для этого необходимо обратиться к Таблице Ордеров Патона.

# Для упрощения контроля тренируюсь на моем акке к кот есть доступ через Личный Кабинет
# Получение Списка ордеров.

# price_orders = exchanges.get_orders_with_price(exchanges.patron_exchange, symbol=SYMBOL, side='buy', price=10)
# print(price_orders)

# Удаление Ордеров по полученным id
# exchanges.cancel_orders_with_price(exchanges.patron_exchange, symbol=SYMBOL, side='buy', price=9.5)

# Получение Коэфициента Копирования для Аккаунта
# rate = exchanges.get_account_rate('')

#Получение Размера Ордера исходя из суммарного Размера у Патрона
# amount = exchanges.get_amount_price_patron_orders(symbol=SYMBOL, side='buy', price=10, account_db_index=0)
# print(amount)

# Копирование Ордеров
exchanges.copy_orders(ordertables_for_copy_clients)






# Создаю Ордера по каждому клиенту
# Если не хватает Добавляю Разницу
# Если больше (то есть минус - то предварительно удаляю все соответсвующие ордера
# И только потом выставляю единый ордер/



# print_json(exchanges.patron_exchange.has)

# exchanges.connect_patron()
# print(type(exchanges.patron_exchange))
# ex = ccxt.bybit
# print((ex))

# print(exchanges.patron_exchange.fetch_balance())
# print(exchanges.patron_exchange.fetch_order_book(SYMBOL))

# # Клиентские Балансы
# for client_name, client_exchange in exchanges.client_exchanges.items():
#     print(client_exchange.fetch_balance(), sep='\n')
# # В одну строку
# # [print(client_exchange.fetch_balance(), sep='\n') for client_name, client_exchange in exchanges.client_exchanges.items()]

# Открытые Ордера
# patron_orders = exchanges.get_account_orders(exchanges.patron_exchange)
# print(patron_orders)

# for client_exchange in exchanges.client_exchanges.values():
#     index = 0
#     client_orders = exchanges.get_account_orders(client_exchange)
#     client_orders['amount'] = -client_orders['amount']
#     print(client_orders, div_line, sep='\n')
#
#     template_orders = patron_orders.copy()
#     template_orders['amount'] = template_orders['amount'] * exchanges.data_base.clients['rate'][index]
#     print(patron_orders, div_line, sep='\n')
#     print(template_orders, div_line, sep='\n')
#     index +=1

# exchanges.client_exchanges['Constantin_ByBit'].create_order(SYMBOL, type='limit', side='buy', price=10, amount=1.7)
# print_json(exchanges.client_exchanges['Constantin_ByBit'].fetch_open_orders(SYMBOL))

# ordertables_for_copy_clients = exchanges.get_ordertables_for_copy_clients(patron_orders)
# print(ordertables_for_copy_clients)






