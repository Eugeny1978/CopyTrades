from connectors.exchanges import Exchanges

SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')
div_line =    '-------------------------------------------------------------------------------------'
double_line = '====================================================================================='



if __name__ == "__main__":

    # Инициализация
    exchanges = Exchanges(SYMBOLS)

    # Удаление Ордеров у Счета Патрона
    exchanges.cancel_account_orders(exchanges.data_base.patron['name'][0], exchanges.patron_exchange, exchanges.symbols)

    # Удаление Ордеров у Счетов Клиентов
    for client, exchange in exchanges.client_exchanges.items():
        exchanges.cancel_account_orders(client, exchange, exchanges.symbols)











