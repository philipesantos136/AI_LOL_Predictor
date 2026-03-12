import sqlite3
c = sqlite3.connect('data/db/lol_datamatches.db').cursor()
c.execute("SELECT AVG(goldat10),AVG(goldat15),AVG(goldat25),AVG(wardsplaced),AVG(visionscore),AVG(cspm) FROM match_data_silver WHERE position='team' AND teamname='FURIA'")
r = c.fetchone()
print(f"goldat10={r[0]} goldat15={r[1]} goldat25={r[2]} wards={r[3]} vision={r[4]} cspm={r[5]}")
