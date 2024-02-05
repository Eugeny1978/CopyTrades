import ccxt
import json

symbols = ('ATOM/USDT', 'BTC/USDT', 'ETH/USDT')

def jprint(data):
    print(json.dumps(data))

ex = ccxt.binance()
# ex = ccxt.bybit()
ex.load_markets()
ex.verbose = True  # uncomment for debugging
def my_overload(symbol, params = {}):
    # your codes go here
    pass

# ex.fetch_ticker = my_overload
# print(ex.fetch_ticker('BTC/USDT'))

# amount_to_precision (symbol, amount):
# price_to_precision (symbol, price):
# cost_to_precision (symbol, cost):
# currency_to_precision (code, amount):
# print(ex.amount_to_precision(symbols[0], 4.56565787878))
# print(ex.price_to_precision(symbols[0], 12.89898989))
# print(ex.cost_to_precision(symbols[0], 16.898893304))


etheur1 = ex.markets['ETH/EUR']
jprint(etheur1)



params = {
    'foo': 'bar',       # exchange-specific overrides in unified queries
    'Hello': 'World!',  # see their docs for more details on parameter names
}

# overrides go in the last argument to the unified call ↓ HERE
# result = ex.fetch_order_book(symbols[0], limit=10, params=params)
# jprint(result)

start_time = ex.parse8601 ('2020-03-01T00:00:00')
print(start_time)
