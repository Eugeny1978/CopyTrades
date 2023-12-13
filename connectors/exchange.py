import ccxt
import pandas as pd                                                 # Объекты DataFrame
from connectors.bitteam import BitTeam
from connectors.data_base import DataBaseRequests, DataBaseErrors


PATRON =  pd.DataFrame('Luchnik_BitTeam' # 'Constantin_BitTeam' # 'Luchnik_Mexc'
# ORDER_TABLE = 'orders_2slabs_mexc'
# BOT_NAME = 'bot_2slabs_bitteam'
# STATUS_TABLE = 'BotStatuses'

class Exchange:
    """
    Соединиться с Биржей
    Получить Лимитные Ордера Патрона (Таблицу Агрегированную по Price + (Buy Sell))
    Получить Лимитные Ордера Клиента (Таблицу Агрегированную по Price + (Buy Sell))
    Сравнить Таблицу Ордера
    """


    def __init__(self, data_base: DataBaseRequests):
        self.data_base = data_base


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
        return df_compact