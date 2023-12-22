import sqlite3 as sq
from data_base.path_to_base import DATABASE

# Run Stop
COPY_BOT = 'Stop'
PATRON_BOT = 'Pause'

def set_bot_statuses():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"UPDATE BotStatuses SET status = '{COPY_BOT}' WHERE bot LIKE 'Copy_bot'")
        curs.execute(f"UPDATE BotStatuses SET status = '{PATRON_BOT}' WHERE bot LIKE 'Patron_bot'")

set_bot_statuses()