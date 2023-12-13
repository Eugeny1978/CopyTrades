import pandas as pd
from connectors.data_base import RequestsDataBase

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

db = RequestsDataBase()

# Получение Аккаунта-Патрона
print(db.patron, div_line, sep='\n')

# Получение Аккаунтов-Клиентов
print(db.clients, div_line, sep='\n')

print(db.__dict__)


