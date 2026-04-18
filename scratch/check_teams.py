import sqlite3

def check_db():
    conn = sqlite3.connect('data/db/lol_datamatches.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    for table in tables:
        try:
            print(f"--- Checking table {table} ---")
            cursor.execute(f"SELECT DISTINCT teamname FROM '{table}' WHERE teamname LIKE 'L%'")
            teams = [t[0] for t in cursor.fetchall()]
            print(f"Teams starting with L: {teams}")
            
            # Check for exactly what the user mentioned (encoded differently maybe)
            cursor.execute(f"SELECT DISTINCT teamname FROM '{table}' WHERE teamname LIKE '%S%'")
            teams_s = [t[0] for t in cursor.fetchall()]
            # print(f"Teams with S: {teams_s}")

        except Exception as e:
            print(f"Error checking {table}: {e}")
            pass
    
    conn.close()

if __name__ == "__main__":
    check_db()
