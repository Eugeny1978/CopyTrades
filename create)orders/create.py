import ccxt
import sqlite3 as sq
import pandas as pd
from connectors.bitteam import BitTeam

from data_base.path_to_base import DATABASE

# Работаю с Аккаунтом
ACCOUNT = 'Luchnik_ByBit'
DB_TABLE = 'Patrons' # 'Clients'

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
        curs.execute(f"SELECT exchange, apiKey, secret FROM '{DB_TABLE}' WHERE name LIKE '{ACCOUNT}'")
        responce = curs.fetchone()
        result = {'exchange': responce['exchange'],
                  'keys': {'apiKey': responce['apikey'], 'secret': responce['secret']}
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

account = get_data_account()
exchange = connects[account['exchange']](account['keys'])
print(get_balance(exchange))
