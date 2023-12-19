from connectors.exchanges import Exchanges
import pandas as pd

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

# Для Отработки Если есть Различия по Объему:
# 1. Получаю список таких ордеров (необходим id - остальное для проверки)
# 2. Удаляю Эти ордера по их ID
# 3. Выставляю Один ордер на полный Объем (для этого необходимо обратиться к Таблице Ордеров Патрона.

# Получаю Первичные Данные (Патрон, Клиенты)
exchanges = Exchanges()

# Получаю Агрегированную Таблицу Ордеров Патрона
# patron_orders = exchanges.get_account_orders(exchanges.patron_exchange)
patron_orders = exchanges.get_patron_ordertable()

# Формирую Словарь Агрегированных Таблиц Ордеров для копирования Клиентами
ordertables_for_copy_clients = exchanges.get_ordertables_for_copy_clients(patron_orders)

# Копирование Ордеров
exchanges.copy_orders(ordertables_for_copy_clients)









