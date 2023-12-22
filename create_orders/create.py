import ccxt
import sqlite3 as sq
import pandas as pd
from connectors.bitteam import BitTeam

from data_base.path_to_base import DATABASE
pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

# Работаю с Аккаунтом
ACCOUNT =  'Luchnik_Okx' # 'Luchnik_ByBit' 'Constantin_ByBit' 'Constantin_GateIo' 'Luchnik_Okx'

SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')

CLIENT_ACCOUNTS = ('Constantin_ByBit', 'Constantin_GateIo', 'Luchnik_Okx') #

connects = {
    'BitTeam': BitTeam,
    'Binance': ccxt.binance,
    'ByBit': ccxt.bybit,
    'Gate_io': ccxt.gateio,
    'Mexc': ccxt.mexc,
    'Okx': ccxt.okx
}

def get_data_account(account_name):
    db_table = 'Patrons' if account_name == 'Luchnik_ByBit' else 'Clients'
    with sq.connect(DATABASE) as connect:
        connect.row_factory = sq.Row  # строки записей в виде dict {}. По умолчанию - кортежи turple ()
        curs = connect.cursor()
        curs.execute(f"SELECT exchange, apiKey, secret, password FROM {db_table} WHERE name LIKE '{account_name}'")
        responce = curs.fetchone()
        result = {
            'exchange': responce['exchange'],
            'keys': {'apiKey': responce['apikey'], 'secret': responce['secret'], 'password': responce['password']}
            }
        return result

def get_balance(exchange):
    balance = exchange.fetch_balance()
    indexes = ['free', 'used', 'total']
    columns = [balance['free'], balance['used'], balance['total']]
    df = pd.DataFrame(columns, index=indexes)
    if exchange == BitTeam:
        df = df.astype(float)
    df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
    return df_compact


def cancel_all_account_orders(account_name):
    data_account = get_data_account(account_name)
    exchange = connects[data_account['exchange']](data_account['keys'])
    for symbol in SYMBOLS:
        exchange.cancel_all_orders(symbol)
    print(account_name, get_balance(exchange), div_line, sep='\n')

def main():

    # # Удаление всех Ордеров на Клиентах. Ордера на патроне Остаются
    # for account in CLIENT_ACCOUNTS:
    #     cancel_all_account_orders(account)

    account = get_data_account(ACCOUNT)
    exchange = connects[account['exchange']](account['keys'])

    # # 'Luchnik_ByBit'
    # exchange.create_market_order(symbol='ATOM/USDT', side='buy', amount=2.2, price=10.7)
    # exchange.create_market_order(symbol='ETH/USDT', side='buy', amount=0.015, price=2200)
    # exchange.create_market_order(symbol='BTC/USDT', side='buy', amount=0.00075, price=43500)

    # # 'Constantin_ByBit'
    # exchange.create_market_sell_order(symbol='SOL/USDT', amount=1.1279)
    # exchange.create_market_sell_order(symbol='XRP/USDT', amount=144.52533)
    # exchange.create_market_sell_order(symbol='DOT/USDT', amount=19.537443)
    # exchange.create_market_sell_order(symbol='XLM/USDT', amount=387.7119)
    # exchange.create_market_sell_order(symbol='BTC/USDT', amount=0.0015)
    # exchange.create_market_buy_order(symbol='ATOM/USDT', amount=3.96) # не отрабатывает просит почему-то цену
    # exchange.create_market_order(symbol='ATOM/USDT', side='buy', amount=3.96, price=10.72)

    # # 'Constantin_GateIo'
    # exchange.create_market_sell_order(symbol='XRP/USDT', amount=23.53579)
    # exchange.create_market_order(symbol='ETH/USDT', side='buy', amount=0.015861, price=2200)
    # exchange.create_market_order(symbol='BTC/USDT', side='buy', amount=0.00081, price=43500)
    # exchange.create_market_sell_order(symbol='ATOM/USDT', amount=3.125)

    # # 'Luchnik_Okx'
    # exchange.create_market_order(symbol='ATOM/USDT', side='buy', amount=3.80785, price=10.7)
    # exchange.create_market_order(symbol='ETH/USDT', side='buy', amount=0.019225, price=2200)
    # exchange.create_market_order(symbol='BTC/USDT', side='buy', amount=0.000981, price=43500)
    # -----
    # exchange.create_order('ATOM/USDT', type='limit', side='buy', amount=1, price=9.0)
    # exchange.create_order('ATOM/USDT', type='limit', side='sell', amount=1, price=13.0)
    # # exchange.create_order('ATOM/USDT', type='limit', side='sell', amount=0.968, price=13.0) # Мин Объем по ATOM = 1
    # exchange.cancel_all_orders('ATOM/USDT') # Для Okx метод не РАБОТАЕТ - вывыливается с ошибкой

    print(get_balance(exchange))



main()
