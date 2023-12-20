import ccxt
import sqlite3 as sq
import pandas as pd
from connectors.bitteam import BitTeam

from data_base.path_to_base import DATABASE
pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

# Работаю с Аккаунтом
ACCOUNT =  'Constantin_Gate' # 'Luchnik_ByBit' 'Constantin_ByBit' 'Constantin_Gate' 'Luchnik_Okx'
DB_TABLE = 'Clients' # 'Patrons' 'Clients'
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')

connects = {
    'BitTeam': BitTeam,
    'Binance': ccxt.binance,
    'ByBit': ccxt.bybit,
    'Gate_io': ccxt.gateio,
    'Mexc': ccxt.mexc,
    'Okx': ccxt.okx
}

def get_data_account():
    with sq.connect(DATABASE) as connect:
        connect.row_factory = sq.Row  # строки записей в виде dict {}. По умолчанию - кортежи turple ()
        curs = connect.cursor()
        curs.execute(f"SELECT exchange, apiKey, secret, password FROM '{DB_TABLE}' WHERE name LIKE '{ACCOUNT}'")
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

def main():
    account = get_data_account()
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

    # # 'Constantin_Gate'
    # exchange.create_market_sell_order(symbol='XRP/USDT', amount=23.53579)
    # exchange.create_market_order(symbol='ETH/USDT', side='buy', amount=0.015861, price=2200)
    # exchange.create_market_order(symbol='BTC/USDT', side='buy', amount=0.00081, price=43500)
    # # Осталось Разобраться почему не в Белом Списке АТОМ
    exchange.create_market_order(symbol='ATOM/USDT', side='buy', amount=3.14148, price=10.7) #

    # # 'Luchnik_Okx'
    # exchange.create_market_order(symbol='ATOM/USDT', side='buy', amount=3.80785, price=10.7)
    # exchange.create_market_order(symbol='ETH/USDT', side='buy', amount=0.019225, price=2200)
    # exchange.create_market_order(symbol='BTC/USDT', side='buy', amount=0.000981, price=43500)


    print(get_balance(exchange))

main()
