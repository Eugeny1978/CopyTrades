from connectors.exchanges import Exchanges
import ccxt
import json

SYMBOL = 'ATOM/USDT'


exchanges = Exchanges()

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

# Ордера Патрона
patron_orders = exchanges.get_patron_orders() # symbol=SYMBOL
orders = exchanges.patron_exchange.fetch_orders()
open_orders = exchanges.patron_exchange.fetch_open_orders()
print(patron_orders)
print(open_orders)
# print(json.dumps(exchanges.patron_exchange.has))



