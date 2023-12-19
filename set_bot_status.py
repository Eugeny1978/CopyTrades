import sqlite3 as sq
from data_base.path_to_base import DATABASE

# Run Stop
BOT = 'Stop'

def set_bot_status():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"UPDATE BotStatus SET status = '{BOT}'")

set_bot_status()