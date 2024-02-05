import os

# Имя Файла Базы Данных
db_name = 'DataBase.db'
db_test = 'DataBase_Test.db'

# Путь к Папке в которой лежит БД
db_dir = os.path.dirname(__file__)

# Путь к Файлу БД
DATABASE = os.path.join(db_dir, db_name)
TEST_DB = os.path.join(db_dir, db_test)
# print(DATABASE)

