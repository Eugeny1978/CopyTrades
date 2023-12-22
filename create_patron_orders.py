import json
import ccxt
import sqlite3 as sq
import pandas as pd
from random import uniform
from time import sleep, localtime, strftime, time

from connectors.bitteam import BitTeam
from data_base.path_to_base import DATABASE

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

# Работаю с Аккаунтом
ACCOUNT =  'Luchnik_ByBit' # 'Luchnik_ByBit' 'Constantin_ByBit' 'Constantin_GateIo' 'Luchnik_Okx'
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')
SPREDS = (2, 3 ,5)
VOLUME = 10
ORDER_PAUSE = 1
PAUSE = 15*60

def print_d(*args):
    print(*args, div_line, sep='\n')

def print_json(data):
    print(json.dumps(data))

def get_bot_status():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT status FROM BotStatuses WHERE bot LIKE 'Patron_bot'")
        return curs.fetchone()[0]

def get_local_time():
        t = localtime()
        current_time = strftime("%H:%M:%S", t)
        return current_time

class PatronBot:
    connects = {
        'BitTeam': BitTeam,
        'Binance': ccxt.binance,
        'ByBit': ccxt.bybit,
        'Gate_io': ccxt.gateio,
        'Mexc': ccxt.mexc,
        'Okx': ccxt.okx
    }

    def __init__(self, account_name, symbols, spreds=(2,3,5), volume=10):
        self.account_name = account_name
        self.spreds = spreds
        self.volume = volume
        self.account_data = self.__get_data_account()
        self.exchange = self.__connect_exchange()
        self.symbols = self.__get_symbol_data(symbols)

    def __get_data_account(self):
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(f"SELECT exchange, apiKey, secret, password FROM Patrons WHERE name LIKE '{self.account_name}'")
            responce = curs.fetchone()
            result = {
                'exchange': responce['exchange'],
                'keys': {'apiKey': responce['apikey'], 'secret': responce['secret'], 'password': responce['password']}
                }
            return result

    def __connect_exchange(self):
        connect = self.connects[self.account_data['exchange']](self.account_data['keys'])
        if not isinstance(connect, BitTeam):
            connect.load_markets()
        return connect

    def __get_accuracy(self, arg: list):
        accuracy = []
        for value in arg:
            value_str = str(value)
            if '.' in value_str:
                accuracy.append(len(value_str.split('.')[1]))
            else:
                accuracy.append(0)
        max_accuracy = max(accuracy)
        return max_accuracy

    def __get_symbol_data(self, symbols):
        symbol_dict = {}
        for symbol in symbols:
            data = self.exchange.fetch_ticker(symbol)
            price_step = self.__get_accuracy([data['open'], data['close'], data['high'], data['low']])
            volume_step = self.__get_accuracy([data['bidVolume'], data['askVolume'], data['baseVolume']])
            symbol_dict[symbol] = {'price_step': price_step, 'volume_step': volume_step}
        return symbol_dict

    def get_start_prices(self):
        start_prices = {}
        for symbol, symbol_data in self.symbols.items():
            data = self.exchange.fetch_ticker(symbol)
            start_price = round(((data['ask'] + data['bid']) / 2), symbol_data['price_step'])
            start_prices[symbol] = start_price
        self.start_prices = start_prices
        return start_prices

    def get_df_orders(self):
        columns = ('symbol', 'level', 'side', 'price', 'amount')
        df_orders = pd.DataFrame(columns=columns)
        for symbol in self.symbols:
            start_price = self.start_prices[symbol]
            price_step = self.symbols[symbol]['price_step']
            volume_step = self.symbols[symbol]['volume_step']
            index = 0
            for spred in self.spreds:
                data = self.get_price_levels(symbol, spred, start_price, price_step)
                buy_amount = self.get_amount(data['buy'], self.get_volume(), volume_step)
                df_orders.loc[len(df_orders)] = [symbol, data['name'], 'buy', data['buy'], buy_amount]
                repeat = 2 if index == 1 else 0
                for t in range(repeat):
                    sell_amount = self.get_amount(data['sell'], self.get_volume(), volume_step)
                    df_orders.loc[len(df_orders)] = [symbol, data['name'], 'sell', data['sell'], sell_amount]
                index += 1
        self.df_orders = df_orders
        return df_orders

    def get_amount(self, price, volume, step):
        return round(volume / price, step)

    def get_price_levels(self, symbol, spred, start_price, price_step):
        price_levels = {}
        price_levels['name'] = f'spred_{spred}'
        delta = 0.01 * spred
        price_levels['sell'] = round(start_price * (1 + delta), price_step)
        price_levels['buy'] = round(start_price * (1 - delta), price_step)
        return price_levels

    def get_volume(self):
        return uniform(1 * self.volume, 1.2 * self.volume)

    def cancel_all_account_orders(self):
        [self.exchange.cancel_all_orders(symbol) for symbol in self.symbols]
        orders = {symbol: self.exchange.cancel_all_orders() for symbol in self.symbols}
        return orders

    def create_orders(self):
        order_ids = []
        for index, order in self.df_orders.iterrows():
            try:
                # exchange.create_order(SYMBOLS[0], type='limit', side='sell', amount=0.88, price=13.5)
                temp_order = self.exchange.create_order(symbol=order['symbol'], type='limit', side=order['side'], price=order['price'], amount=order['amount'])
                # ByBit возвращает только корректный ID остальную инфу - ставит None. Поэтому использую входные данные для печати
                info = f"ID={temp_order['id']}, {order['symbol']}, {order['side'].upper()}, price={order['price']}, amount={order['amount']}"
                print(f"Создан Ордер: | {info}")
                order_ids.append(temp_order['id'])
            except:
                info = f"{order['symbol']}, {order['side'].upper()}, price={order['price']}, amount={order['amount']}"
                print(f'НЕ получилось создать Ордер: | {info}')
            sleep(ORDER_PAUSE)
        self.order_ids = order_ids
        return order_ids

    def get_open_orders(self):
        orders = []
        for symbol in self.symbols:
            try:
                order_list = self.exchange.fetch_open_orders(symbol)
                for order in order_list:
                    orders.append(order)
            except:
                print(f'API Биржи: Не удалось Получить список Ордеров.')
        return self.convert_orders_to_df(orders)

    def convert_orders_to_df(self, orders):
        columns = ('id', 'symbol', 'type', 'side', 'price', 'amount')
        df = pd.DataFrame(columns=columns)
        for order in orders:
            # для BitTeam - другие Столбцы
            df.loc[len(df)] = [order['id'], order['symbol'], order['type'], order['side'], order['price'], order['amount']]
            #df.groupby(['symbol', 'type', 'side', 'price']).sum().reset_index()
        return df

    def get_balance(self):
        balance = self.exchange.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        if self.exchange == BitTeam:
            df = df.astype(float)
        df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
        return df_compact


def main():

    patron = None
    # 0. Инициализация: Данные Аккаунта из БД / Соединение с Биржей / Данные по Торгуемым Парам
    if get_bot_status() == 'Run':
        patron = PatronBot(ACCOUNT, SYMBOLS, SPREDS, VOLUME)
        print_d(f'Аккаунт: {ACCOUNT} | {get_local_time()}', f'Биржа: {patron.exchange}')

    while get_bot_status() == 'Run':
        start_time = time()

        # 1. Стартовые Цены
        patron.get_start_prices()
        print_d(f'Старт-Цены:',  patron.start_prices)

        # 2. Формирование Таблицы Ордеров
        patron.get_df_orders()
        print_d(f'Таблица Ордеров:', patron.df_orders)

        # 3. Удаление Устаревших Ордеров
        temp_orders = patron.cancel_all_account_orders()
        for symbol, order_data in temp_orders.items():
            info = order_data if len(order_data) else 'Открытых Ордеров НЕТ'
            print_d(f'{symbol}:', info)

        # 4. Создание Новых Ордеров
        patron.create_orders()

        # 5. Таблица Открытых Ордеров на Бирже:
        open_orders = patron.get_open_orders()
        print_d(div_line, f"Таблица Открытых Ордеров на Бирже:", open_orders)

        # 6. Баланс Аккаунта:
        balance = patron.get_balance()
        print_d(f"Баланс Аккаунта:", balance)

        # Время Выполнения
        print(f'Выполнено за {round(time() - start_time, 3)} сек.')

        # Пауза между Изменениями
        pause = round(PAUSE/60)
        print(f'Выполняется Пауза {pause} мин. | {get_local_time()}')
        sleep(PAUSE)
        print_d(f'Пауза Завершена. | {get_local_time()}', div_line)

    match patron, get_bot_status():
        case True, 'Stop':
            patron.cancel_all_account_orders()
            print(f'Ордера ОТМЕНЕНЫ. | {get_local_time()}')
        case True, 'Pause':
            print(f'Режим ПАУЗА. Выставленные ранее Ордера все еще на Бирже. | {get_local_time()}')
        case True, _:
            print(f'БОТ ОСТАНОВЛЕН. | {get_local_time()}')
        case _:
            print("Процесс не был запущен. Измените статус 'Patron_bot' на значение 'Run'")

main()