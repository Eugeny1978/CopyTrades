import pandas as pd                     # Объекты DataFrame
import sqlite3 as sq                    # Работа с Базой Данных
from data_base.path_to_base import DATABASE
import ccxt
import json

MIN_USDT = 500


def get_clients():
    with sq.connect(DATABASE) as connect:
        connect.row_factory = sq.Row
        curs = connect.cursor()
        curs.execute(f"SELECT * FROM Clients")
        return curs.fetchall()

connects = {
    'Binance': ccxt.binance,
    'BitTeam': ccxt.bitteam,
    'ByBit': ccxt.bybit,
    'GateIo': ccxt.gateio,
    'Mexc': ccxt.mexc,
    'Okx': ccxt.okx
}

def connect_exchange(client: sq.Row):
    keys = {'apiKey': client['apiKey'],
            'secret': client['secret'],
            'password': client['password']
            }
    return connects[client['exchange']](keys)

def get_balance_USDT(exchange):
    balance = exchange.fetch_balance()
    try:
        usdt = balance['total']['USDT']
    except:
        usdt = 0
    return usdt

def get_rate_value(usdt):
    rate = round(usdt/MIN_USDT, 1)
    if rate < 1: rate = 1
    return rate

def update_rates_sql(list_rates_clients):
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        for client in list_rates_clients:
            curs.execute(f"UPDATE Clients SET rate == {client['rate']} WHERE name IS '{client['name']}'")


if __name__ == '__main__':

    clients = get_clients()
    list_new_rates_clients = []
    for client in clients:
        c = {}
        exchange = connect_exchange(client)
        balance_usdt = get_balance_USDT(exchange)
        c['name'], c['rate'] = client['name'], get_rate_value(balance_usdt)
        list_new_rates_clients.append(c)
    print(*list_new_rates_clients, sep='\n')

    update_rates_sql(list_new_rates_clients)









