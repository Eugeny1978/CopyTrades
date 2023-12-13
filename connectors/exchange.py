import ccxt
import pandas as pd             # Объекты DataFrame
from connectors.bitteam import BitTeam
from connectors.data_base import RequestsDataBase

# ACCOUNT =  'Luchnik_BitTeam' # 'Constantin_BitTeam' # 'Luchnik_Mexc'
# ORDER_TABLE = 'orders_2slabs_mexc'
# BOT_NAME = 'bot_2slabs_bitteam'
# STATUS_TABLE = 'BotStatuses'

class Exchange():

    def __init__(self, data_base: RequestsDataBase):
        self.data_base = data_base
        self.exchange = self.connect_exchange()

    def __str__(self):
        return self.data_base.exchange

    def connect_exchange(self):
        keys = self.data_base.apikeys
        match self.data_base.exchange:
            case 'BitTeam':
                exchange = BitTeam(keys)
            case 'Binance':
                exchange = ccxt.binance(keys)
            case 'Mexc':
                exchange = ccxt.mexc(keys)
            case 'Bybit':
                exchange = ccxt.bybit(keys)
            case _:
                print(f'Биржа | {self.data_base.exchange} | не прописана в функции connect_exchange()')
                raise
        if not isinstance(exchange, BitTeam):
            exchange.load_markets()
        return exchange

    def get_balance(self):
        balance = self.exchange.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        if self.data_base.exchange == 'BitTeam':
            df = df.astype(float)
        df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
        # df_compact = df_0.loc[:, (df_0 != '0').any(axis=0)]  # если числа в виде строк
        return df_compact