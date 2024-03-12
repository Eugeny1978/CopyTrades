import json                     # Вывод в виде JSON объектов (для анализа результатов запросов при отладке)
import pandas as pd             # Работа с DataFrame
import sqlite3 as sq            # Работа с Базой Данных
from data_base.path_to_base import DATABASE, TEST_DB # Путь к Базам Данных (Рабочая, Тестовая)
import ccxt                     # REST Запросы к Биржам
from datetime import datetime, timedelta # Работа с Датой и Временем
from time import sleep, time    # Работа с Временем (Паузы, Интервалы)


pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30 # Макс Кол-во Отображаемых Cтрок

div_line = '-' * 120
FORMAT_dt = '%Y-%m-%d %H:%M:%S'
SYMBOLS_liquid = ('ATOM/USDT', 'BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'TRX/USDT', 'XLM/USDT', 'DOT/USDT', 'ARB/USDT', 'APT/USDT')
SYMBOLS_shit = ('DEL/USDT',)
PATRON_liquid = 'Constantin_ByBit'
PATRON_shit = 'Constantin_Mexc'

DATABASE = DATABASE
TRADE_TYPE = 'Shit_coins'
BOT_NAME = 'Copy_shit_market'
INTERVAL = 60 # интервал между просмотром свежих сделок у Патрона
PAUSE = 1 # пуаза между обработкой
DELTA_MIN = 60 # Интервал, вглубь которого проверяется наличие новых Сделок:


connections = {
    'Binance': ccxt.binance,
    'BitTeam': ccxt.bitteam,
    'ByBit': ccxt.bybit,
    'GateIo': ccxt.gateio,
    'Mexc': ccxt.mexc,
    'Okx': ccxt.okx
}

def get_bot_status():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT status FROM BotStatuses WHERE bot LIKE '{BOT_NAME}'")
        return curs.fetchone()[0]

def connect_exchange(account):
    try:
        connection: ccxt.Exchange = connections[account['exchange']]() # {'options': {'defaultType': 'spot'}}
        connection.load_markets()
        # connection.options['defaultType'] = 'spot'
        # connection.enableRateLimit = True # по умолчанию уже стоит
        connection.apiKey = account['apiKey']
        connection.secret = account['secret']
        connection.password = account['password']
        return connection
    except:
        print(f"{account['name']} | {account['exchange']} | НЕ Удалось подключиться. Проверьте API Ключи.")
        return None

def form_datetime(dt: str):
    dt = ' '.join(dt.split('.')[:-1])
    dt = ' '.join(dt.split('T'))
    return dt

def get_dt_now():
    dt_now = datetime.now()
    dt_str = dt_now.strftime(FORMAT_dt)
    return dt_str

class ClientData:

    def __init__(self, trade: str): # 'Liquid_coins', 'Shit_coins'
        self.trade = trade
        self.exchanges, self.db_table = self.get_exchanges()
        self.clients = self.get_clients()

    def get_exchanges(self):
        match self.trade:
            case 'Liquid_coins':
                exchanges = ('ByBit', 'Binance', 'GateIo', 'Okx')
                table = 'Clients'
            case 'Shit_coins':
                exchanges = ('BitTeam', 'Mexc')
                table = 'Clients_Mexc'
        return exchanges, table

    def get_clients(self):
        row_exchanges = '\', \''.join(self.exchanges)
        query = (f"""
         SELECT name, exchange, rate, apiKey, secret, password 
         FROM {self.db_table} 
         WHERE exchange IN ('{row_exchanges}') 
             AND status IS 'Active' 
         """)
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(query)
            return curs.fetchall()

class Trader:

    def __init__(self, client: sq.Row):
        self.client = client
        self.connection: ccxt.Exchange = connect_exchange(client)
        self.balance =  self.get_balance()

    def get_balance(self):
        if not self.connection:
            return None
        balance = self.connection.fetch_balance()
        indexes = ['free', 'used', 'total']
        columns = [balance['free'], balance['used'], balance['total']]
        df = pd.DataFrame(columns, index=indexes)
        return df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями

    def get_amount_coin(self, coin):
        try:
            return self.balance[coin]['free']
        except:
            return 0

    def market_order(self, symbol: str, amount: float, side: str):
        # Патрон должен покупать мин на 11 USDT чб в случ падения цены сохр условие мин Лота
        order_side = {'sell': self.connection.create_market_sell_order,
                      'buy': self.connection.create_market_buy_order}
        text = f"{symbol}, {side.upper()}, Объем: {amount} | "
        try:
            order_side[side](symbol=symbol, amount=amount)
            print(text, "УСПЕШНО создан по РЫНКУ")
        except:
            print(text, f"НЕ Удалась создать по рынку! XXX")

class PatronData:

    def __init__(self, trade: str): # 'Liquid_coins', 'Shit_coins'
        self.name, self.symbols, self.db_table, self.db_trades = self.get_constantes(trade)
        self.patron  = self.get_patron()
        self.connection: ccxt.Exchange = connect_exchange(self.patron)

    def get_constantes(self, trade: str):
        match trade:
            case 'Liquid_coins':
                name = PATRON_liquid
                symbols = SYMBOLS_liquid
                db_table = 'Patrons'
                db_trades = 'MarketTrades'
            case 'Shit_coins':
                name = PATRON_shit
                symbols = SYMBOLS_shit
                db_table = 'Patrons_Mexc'
                db_trades = 'MarketTrades_Mexc'
        return name, symbols, db_table, db_trades

    def get_patron(self):
        query = (f"""
         SELECT name, exchange, apiKey, secret, password 
         FROM {self.db_table} 
         WHERE name IS '{self.name}'
         """)
        with sq.connect(DATABASE) as connect:
            connect.row_factory = sq.Row  # Строки записей в виде dict {}. По умолчанию - кортежи turple ()
            curs = connect.cursor()
            curs.execute(query)
            return curs.fetchone()

    def not_id_trade_db(self, id):
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"""SELECT * FROM {self.db_trades} WHERE id IS '{id}'""")
            responce = curs.fetchone()
            not_trade = False if responce else True
            return not_trade

    def record_id_trade(self, trade: dict):
        with sq.connect(DATABASE) as connect:
            curs = connect.cursor()
            curs.execute(f"""INSERT INTO {self.db_trades} (symbol, id, side, amount, cost, price, datetime, timestamp) 
            VALUES (
            '{trade['symbol']}', 
            '{trade['id']}', 
            '{trade['side']}', 
            {trade['amount']}, 
            {trade['cost']}, 
            {trade['price']}, 
            '{trade['datetime']}', 
            {trade['timestamp']})""")

    def get_new_trades(self):
        # start_dt = str(datetime.now(tz=pytz.UTC) - timedelta(minutes=DELTA_MIN))
        start_dt = str(datetime.utcnow() - timedelta(minutes=DELTA_MIN))
        # start_stamp = mktime(start_dt.timetuple()) # Нужно * 1000 чб получить время по которому сравниваем. не стоку а дату
        start_stamp = self.connection.parse8601(start_dt) # встроенный метод
        new_trades = []
        for symbol in self.symbols:
            try:
                last_trades = self.connection.fetch_my_trades(symbol=symbol, since=start_stamp)
            except Exception as error:
                print(error)
                print(f"Запрос не был Обработан Биржей. Проверьте Синхронизацию Времени")
                continue
            if len(last_trades):
                for trade in last_trades:
                    if trade['takerOrMaker'] == 'taker': # trade['type'] == 'market'
                        if self.not_id_trade_db(trade['id']):
                            trade_info = {'symbol': symbol,
                                          'id': trade['id'],
                                          'side': trade['side'],
                                          'amount': trade['amount'],
                                          'cost': round(trade['cost'], 1),
                                          'price': trade['price'],
                                          'datetime': form_datetime(trade['datetime']),
                                          'timestamp': trade['timestamp']}
                            new_trades.append(trade_info)
                            self.record_id_trade(trade_info)
        return new_trades

    def get_price_amount_for_trade(self, symbol, cost_usdt):
        price = self.connection.fetch_ticker(symbol)['last']
        amount = float(self.connection.amount_to_precision(symbol, (cost_usdt / price)))
        return (price, amount)


if __name__ == '__main__':

    was_run = False
    if get_bot_status() == 'Run':
        print(get_dt_now(), 'Процесс Копирования Сделок ПО РЫНКУ ЗАПУЩЕН.', sep=' | ')
        # БЛОК: КАКИЕ COINs НЕОБХОДИМО продать ПО РЫНКУ. Смотрю свежие Сделки ПО РЫНКУ Патрона
        patron = PatronData(TRADE_TYPE)
        was_run = True
    else:
        print("Процесс НЕ был запущен. Измените статус Бота на значение 'Run'")

    # # БЛОК Предварительно Куплю и Продам для Тестов
    # symbol_s, cost_usdt_s = 'ATOM/USDT', 10
    # symbol_b, cost_usdt_b = 'ETH/USDT', 10
    # price_s, amount_s = patron.get_price_amount_for_trade(symbol_s, cost_usdt_s)
    # price_b, amount_b = patron.get_price_amount_for_trade(symbol_b, cost_usdt_b)
    # print(f"{symbol_s = } | {price_s = } | {amount_s = }")  ###
    # print(f"{symbol_b = } | {price_b = } | {amount_b = }")  ###
    # sell_trade = patron.connection.create_market_sell_order(symbol=symbol_s, amount=amount_s)
    # buy_trade = patron.connection.create_market_buy_order(symbol=symbol_b, amount=amount_b)
    # print(json.dumps(buy_trade)) # проверил сделка проходит. Дает инфу только buy_trade['id']. Остальные Поля = Null
    # print(json.dumps(sell_trade)) # проверил сделка проходит. Дает инфу только sell_trade['id']. Остальные Поля = Null

    while get_bot_status() == 'Run':

        new_deals = patron.get_new_trades()

        if not new_deals:
            print(get_dt_now(), f"За последние {DELTA_MIN} мин. Новых Необработанных Сделок НЕТ", f"Пауза {INTERVAL} сек.", sep=' | ')
            sleep(INTERVAL)
            continue
        else:
            start_dt = time()
            print(get_dt_now(), f"За последние {DELTA_MIN} мин. Есть НОВЫЕ (необработанные) Сделки ПО РЫНКУ:", sep=' | ')
            print(*new_deals, div_line, sep='\n')

            # Клиенты
            clients = ClientData(TRADE_TYPE).clients

            # Обход Клиентов
            for client in clients:
                print(f"{client['name']} | {client['exchange']} | {get_dt_now()}", div_line, sep='\n')

                trader = Trader(client) # Подготовка к Торговле
                if not trader.connection:
                    continue
                print(f"Баланс ПЕРЕД Изменением:", trader.balance, div_line, sep='\n')

                # Обход Свежих сделок
                for deal in new_deals:
                    symbol = deal['symbol']
                    coin = symbol.split('/')[0]
                    price_usdt = trader.connection.fetch_ticker(symbol)['last'] # нужно ли каждому узнеавать или один раз
                    match deal['side']:
                        case 'sell': # Продажа ПО РЫНКУ
                            amount_coin = trader.get_amount_coin(coin)
                            cost_usdt = round(price_usdt * amount_coin, 2)
                            if cost_usdt > 10.1:
                                trader.market_order(symbol=symbol, amount=amount_coin, side='sell')
                            else:
                                print(f"{symbol}, {deal['side'].upper()}, Объем: {amount_coin} | Недостаточно средств!")
                        case 'buy': # Покупка ПО РЫНКУ
                            amount_coin = deal['amount'] * trader.client['rate']
                            amount_coin_r = trader.connection.amount_to_precision(symbol, amount_coin)
                            trader.market_order(symbol=symbol, amount=amount_coin_r, side='buy')
                print(div_line)
                sleep(PAUSE)
                print(f"Баланс ПОСЛЕ Изменений:", trader.get_balance(), div_line, div_line, sep='\n')
                sleep(PAUSE)
            print(f'Клиенты Обработаны за {round(time() - start_dt, 3)} сек.', (' |' * 5))

    if get_bot_status() != 'Run' and was_run:
        print(get_dt_now(), f"Контроль за Сделками по РЫНКУ Отключен.", sep=' | ')