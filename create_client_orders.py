from time import sleep
from random import uniform
from copy_trades import Exchanges

PAUSE = 1           # Пауза между Запросами
ACCOUNT_PAUSE = 2   # Пауза между Обработкой Клиентов
SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')  # Сравнение по Торгуемым Парам
div_line =    '-------------------------------------------------------------------------------------'
double_line = '====================================================================================='

def main():
    # Инициализация
    exchanges = Exchanges(SYMBOLS)

    for client, exchange in exchanges.client_exchanges.items():

        nominal_price = 9.5
        nominal_amount = 1.2
        price_atom = uniform(0.9 * nominal_price, 1 * nominal_price)
        amount_atom = uniform(0.9 * nominal_amount, 1 * nominal_amount)
        exchange.create_order(symbol='ATOM/USDT', type='limit', side='buy', price=price_atom, amount=amount_atom)
        sleep(PAUSE)

        nominal_price = 42500
        nominal_amount = 0.0005
        price_btc = uniform(0.9 * nominal_price, 1 * nominal_price)
        amount_btc = uniform(0.9 * nominal_amount, 1 * nominal_amount)
        exchange.create_order(symbol='BTC/USDT', type='limit', side='buy', price=price_btc, amount=amount_btc)
        sleep(PAUSE)

        nominal_price = 2400
        nominal_amount = 0.007
        price_eth = uniform(0.9 * nominal_price, 1 * nominal_price)
        amount_eth = uniform(0.9 * nominal_amount, 1 * nominal_amount)
        exchange.create_order(symbol='ETH/USDT', type='limit', side='buy', price=price_eth, amount=amount_eth)
        sleep(PAUSE)

        sleep(ACCOUNT_PAUSE)



main()