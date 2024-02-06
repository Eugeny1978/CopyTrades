import pandas as pd
import ccxt

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30 # Макс Кол-во Отображаемых Cтрок
div_line = '-' * 120

CONNECTION = ccxt.bybit()

def parse_timestamp(dt: str):
    timestamp = CONNECTION.parse8601(dt)
    return timestamp

def dprint(data):
    print(data, div_line, sep='\n')

def create_trade(symbol: str, id: str, side: str, cost: float, price: float, dt: str):
    return {'symbol': symbol,
             'id': id,
             'side': side,
             'amount': round(cost/price, 5),
             'cost': cost,
             'price': price,
             'datetime': dt,
             'timestamp': parse_timestamp(dt)}

trade11 = create_trade("ATOM/USDT", '00011', 'buy', 10, 9.07, '2024-02-05 16:52:42')
trade12 = create_trade("ATOM/USDT", '00012', 'sell', 15, 8.98, '2024-02-05 16:53:02')
trade13 = create_trade("ATOM/USDT", '00013', 'buy', 12, 9.09, '2024-02-05 16:53:07')
trade14 = create_trade("ATOM/USDT", '00014', 'sell', 10, 8.99, '2024-02-05 16:58:22')
trade15 = create_trade("ATOM/USDT", '00015', 'buy', 20, 9.04, '2024-02-05 16:59:48')
trade16 = create_trade("ATOM/USDT", '00015', 'buy', 10, 9.07, '2024-02-05 17:01:18')

trade21 = create_trade("BTC/USDT", '00021', 'sell', 10, 38380.4, '2024-02-05 16:57:22')
trade31 = create_trade("ETH/USDT", '00031', 'sell', 10, 2299.74, '2024-02-05 16:59:36')






if __name__ ==  '__main__':
    trades = [trade11, trade12, trade13, trade14, trade15, trade16, trade21, trade31]
    print(*trades, sep='\n')
    # columns = ('symbol', 'id', 'side', 'amount', 'cost', 'price', 'datetime', 'timestamp')
    # df = pd.DataFrame(columns=columns)
    # for trade in trades:
    #     df.loc[len(df)] = trade
    # print(df, div_line, sep='\n')
    df = pd.DataFrame(trades)
    dprint(df)

    df1 = df.groupby(['symbol', 'side']).agg({'cost': ['sum']}).reset_index()
    dprint(df1)
    df2 = df.groupby(['symbol', 'side']).agg({'cost': ['sum', 'mean'], 'timestamp': ['min']}).reset_index()
    dprint(df2)

