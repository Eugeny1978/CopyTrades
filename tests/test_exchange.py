from connectors.exchanges import Exchanges
import ccxt

SYMBOL = 'ETH/USDT'


exchanges = Exchanges()

# exchanges.connect_patron()
# print(type(exchanges.patron_exchange))
# ex = ccxt.bybit
# print((ex))

# print(exchanges.patron_exchange.fetch_balance())
# print(exchanges.patron_exchange.fetch_order_book(SYMBOL))

# Клиентские Балансы
for client_name, client_exchange in exchanges.client_exchanges.items():
    print(client_exchange.fetch_balance(), sep='\n')
# В одну строку
# [print(client_exchange.fetch_balance(), sep='\n') for client_name, client_exchange in exchanges.client_exchanges.items()]



