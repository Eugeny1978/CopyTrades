import pandas as pd
from connectors.data_base import DataBaseRequests

pd.options.display.width= None # Отображение Таблицы на весь Экран
pd.options.display.max_columns= 20 # Макс Кол-во Отображаемых Колонок
div_line = '-----------------------------------------------------------------------------------------------------'

db = DataBaseRequests()

# Получение Аккаунта-Патрона
print(db.patron, div_line, sep='\n')

# Получение Аккаунтов-Клиентов
print(db.clients, div_line, sep='\n')

# print(db.__dict__)

# Получение Имени Биржы у Патрона
print(db.patron['exchange'][0], div_line, sep='\n')
