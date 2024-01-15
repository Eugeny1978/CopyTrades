import ccxt
import json

SYMBOL = 'ATOM/USDT'

exchange = ccxt.gateio()
# ticker = exchange.fetch_ticker(SYMBOL)
# print(json.dumps(ticker))
orderbook = exchange.fetch_order_book(SYMBOL, limit=10)
print('GATE --------------')
print(json.dumps(orderbook))

# exchange = ccxt.okx()
# orderbook = exchange.fetch_order_book(SYMBOL, limit=5)
# print('OKX --------------')
# print(json.dumps(orderbook))
#
# exchange = ccxt.bybit()
# orderbook = exchange.fetch_order_book(SYMBOL, limit=5)
# print('BYBIT --------------')
# print(json.dumps(orderbook))

bids = orderbook['bids']
prices = [bid[0] for bid in bids]
volumes = [bid[1] for bid in bids]
print(prices, volumes, sep='\n')





