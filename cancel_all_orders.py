from connectors.exchanges import Exchanges

SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')
div_line =    '-------------------------------------------------------------------------------------'
double_line = '====================================================================================='


def cancel_orders(account_name, exchange, symbols):
    match exchange.name:
        case 'OKX':
            order_ids = []
            for symbol in symbols:
                order_list = exchange.fetch_open_orders(symbol)
                for order in order_list:
                    order_ids.append({'id': order['id'], 'symbol': symbol})
            print(f'{account_name} | Будут Удалены Все Ордера:')
            for order in order_ids:
                exchange.cancel_order(order['id'], order['symbol'])
                print(order['symbol'], order['id'])
            print(div_line)
        case _:
            for symbol in symbols:
                exchange.cancel_all_orders(symbol)
            print(f'{account_name} | Удалены Все Ордера', div_line, sep='\n')


if __name__ == "__main__":

    # Инициализация
    exchanges = Exchanges(SYMBOLS)

    # Удаление Ордеров у Счета Патрона
    cancel_orders(exchanges.data_base.patron['name'][0], exchanges.patron_exchange, exchanges.symbols)

    # Удаление Ордеров у Счетов Клиентов
    for client, exchange in exchanges.client_exchanges.items():
        cancel_orders(client, exchange, exchanges.symbols)











