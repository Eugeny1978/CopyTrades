from connectors.exchanges import Exchanges

SYMBOLS = ('ATOM/USDT', 'ETH/USDT', 'BTC/USDT')
div_line =    '-------------------------------------------------------------------------------------'
double_line = '====================================================================================='

if __name__ == "__main__":

    # Инициализация
    exchanges = Exchanges(SYMBOLS)

    # Закуп и Откуп Крипты
    for client, exchange in exchanges.client_exchanges.items():
        if client == 'Constantin_ByBit':
            pass
        #     print('продаю для Constantin_ByBit')
        #     exchange.create_market_order(symbol='ATOM/USDT', side='sell', amount=17.4)
        #     exchange.create_market_order(symbol='BTC/USDT', side='sell', amount=0.0046)
        #     exchange.create_market_order(symbol='ETH/USDT', side='sell', amount=0.034)
        #     exchange.create_market_order(symbol='XLM/USDT', side='sell', amount=813.5975)

        if client == 'Constantin_Gate':
            pass
            # print('покупаю для Constantin_Gate')
            # exchange.create_market_order(symbol='ATOM/USDT', side='buy', amount=3.3, price=10)
            # exchange.create_market_order(symbol='BTC/USDT', side='buy', amount=0.00078, price=42500)
            # exchange.create_market_order(symbol='ETH/USDT', side='buy', amount=0.0134, price=2500)

        if client == 'Luchnik_Okx':
            pass
            # print('продаю для Luchnik_Okx')
            # exchange.create_market_order(symbol='ATOM/USDT', side='sell', amount=4)
            # exchange.create_market_order(symbol='BTC/USDT', side='sell', amount=0.0005)
            # exchange.create_market_order(symbol='ETH/USDT', side='sell', amount=0.0025)


