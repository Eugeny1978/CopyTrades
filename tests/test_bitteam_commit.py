from connectors.bitteam import BitTeam
from connectors.logic_errors import LogicErrors
SYMBOL = 'DEL/USDT'

exchange = BitTeam()
order_book = exchange.fetch_order_book(SYMBOL)
print(order_book)

