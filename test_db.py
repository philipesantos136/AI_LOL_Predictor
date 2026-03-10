import sqlite3
import pandas as pd
from pprint import pprint

conn = sqlite3.connect('data/db/lol_datamatches.db')
df = pd.read_sql("SELECT playername, champion, teamkills, dragons, towers, gamelength FROM match_data_silver WHERE position != 'team' AND champion IS NOT NULL LIMIT 5", conn)
print("PLAYER ROWS:")
print(df)

df2 = pd.read_sql("SELECT teamname, teamkills, dragons, towers, gamelength FROM match_data_silver WHERE position == 'team' LIMIT 5", conn)
print("\nTEAM ROWS:")
print(df2)
conn.close()
