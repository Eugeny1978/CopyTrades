from connectors.exchanges import Exchanges
import ccxt
import json
import pandas as pd

# SYMBOL = 'ATOM/USDT'
# SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

def print_json(data):
    print(json.dumps(data))

def print_p(*data):
    print(*data, div_line, sep='\n')

# Получаю Первичные Данные (Патрон, Клиенты)
exchanges = Exchanges()

# Акк ПАТРОН
patron_balance = exchanges.get_balance(exchanges.patron_exchange)
patron_orders = exchanges.get_patron_ordertable()

print(f"Акк. ПАТРОН: | Биржа: {exchanges.patron_exchange}")
print_p(f"Баланс:", patron_balance)
print_p(f"Ордера: ", patron_orders)
print_p('\n')

# Акк-ты КЛИЕНТЫ
print_p(f"Акк-ты Клиенты:")
for exchange_name, client_exchange in exchanges.client_exchanges.items():
    client_balance = exchanges.get_balance(client_exchange)
    client_orders = 0
    print_p(f"Акк. {exchange_name} | Биржа: {client_exchange}", client_balance)

ordertables_for_copy_clients = exchanges.get_ordertables_for_copy_clients(patron_orders)
for table in ordertables_for_copy_clients:
    print_p(table)