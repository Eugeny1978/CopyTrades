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

# Получаю Первичные Данные (Патрон, Клиенты)
exchanges = Exchanges()

# Акк ПАТРОН
patron_balance = exchanges.get_balance(exchanges.patron_exchange)
print(f"Акк. ПАТРОН: | Биржа: {exchanges.patron_exchange}")
print(patron_balance, div_line, div_line, sep='\n')

# Акк-ты КЛИЕНТЫ
print(f"Акк-ты Клиенты:", div_line, sep='\n')
for exchange_name, client_exchange in exchanges.client_exchanges.items():
    client_balance = exchanges.get_balance(client_exchange)
    print(f"Акк. {exchange_name} | Биржа: {client_exchange}", sep='\n')
    print(client_balance, div_line, sep='\n')
