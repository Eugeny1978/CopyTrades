import ccxt
import sqlite3 as sq

from data_base.path_to_base import DATABASE

ACCOUNT = 'Luchnik_ByBit'
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT', 'LINK/USDT')

config = {
    'create': True,
    'cancel': True,
}

def get_api_keys(account_name):
    with sq.connect(DATABASE) as connect:
        connect.row_factory = sq.Row  # строки записей в виде dict {}. По умолчанию - кортежи turple ()
        curs = connect.cursor()
        curs.execute("""SELECT * FROM Apikeys WHERE account LIKE ?""", [account_name])
        account = curs.fetchone()
        keys = {'apiKey': account['apikey'], 'secret': account['secret']}
        return keys

keys = get_api_keys(ACCOUNT)
exchange = ccxt.bybit(keys)

if config['cancel']:
    for symbol in SYMBOLS:
        exchange.cancel_all_orders(symbol)

if config['create']:
    exchange.create_order(SYMBOLS[0], type='limit', side='buy', amount=1.7, price=9.2)
    exchange.create_order(SYMBOLS[0], type='limit', side='buy', amount=1.2, price=9.2)
    exchange.create_order(SYMBOLS[0], type='limit', side='buy', amount=1.1, price=9.2)
    exchange.create_order(SYMBOLS[0], type='limit', side='sell', amount=0.88, price=13.5)

    exchange.create_order(SYMBOLS[1], type='limit', side='buy', amount=0.007, price=2000)
    exchange.create_order(SYMBOLS[1], type='limit', side='buy', amount=0.005, price=1950)

    exchange.create_order(SYMBOLS[2], type='limit', side='buy', amount=0.0004, price=37000)
    exchange.create_order(SYMBOLS[2], type='limit', side='buy', amount=0.0005, price=36000)

    exchange.create_order(SYMBOLS[3], type='limit', side='buy', amount=1.2, price=12.9)


