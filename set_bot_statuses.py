import sqlite3 as sq
from datetime import datetime
from data_base.path_to_base import DATABASE, TEST_DB # Рабочая и Тестовая Базы

DATABASE = DATABASE
# Run Pause, Stop
COPY_BOT = 'Run'
COPY_BOT_MECX = 'Run'
COPY_LIQUID_MARKET = 'Run'

COPY_SHIT_MARKET = 'Stop'

PATRON_BOT = 'Stop'


def set_bot_statuses():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"UPDATE BotStatuses SET status = '{COPY_BOT}' WHERE bot LIKE 'Copy_bot'")
        curs.execute(f"UPDATE BotStatuses SET status = '{COPY_BOT_MECX}' WHERE bot LIKE 'Copy_bot_Mexc'")
        curs.execute(f"UPDATE BotStatuses SET status = '{PATRON_BOT}' WHERE bot LIKE 'Patron_bot'")
        curs.execute(f"UPDATE BotStatuses SET status = '{COPY_LIQUID_MARKET}' WHERE bot LIKE 'Copy_liquid_market'")
        curs.execute(f"UPDATE BotStatuses SET status = '{COPY_SHIT_MARKET}' WHERE bot LIKE 'Copy_shit_market'")

set_bot_statuses()
print(f"Выполнено в: {datetime.now().strftime('%Y-%m-%d | %H:%M:%S')}")