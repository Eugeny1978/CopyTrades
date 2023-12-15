from connectors.exchanges import Exchanges
import ccxt
import json
import pandas as pd

SYMBOL = 'ATOM/USDT'
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

def print_json(data):
    print(json.dumps(data))


exchanges = Exchanges()

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
patron_orders = exchanges.get_account_orders(exchanges.patron_exchange)
print(patron_orders)

for client_exchange in exchanges.client_exchanges.values():
    client_orders = exchanges.get_account_orders(client_exchange)
    print(client_orders)

# ddd = {
#     'name1': 'val1',
#     'name2': 'val2',
#     'name3': 'val3',
#     'name4': 'val4',
#     'name5': 'val5',
# }
#
# print(*ddd)





