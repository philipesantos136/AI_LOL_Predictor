import sqlite3

def fix_team_name():
    db_file = 'data/db/lol_datamatches.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # We'll use a broad pattern to find the broken name
    # Usually it's 'L' followed by weird chars then 'S'
    # Based on the user's report 'LÃ˜S'
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    mapping = {
        # The exact data might vary depending on how Python/SQLite handles the encoding
        # so we use LIKE with wildcards to be safe, or just provide the common broken versions
        "LÃ˜S": "Los Grandes",
        "LS": "Los Grandes"
    }
    
    total_updated = 0
    
    for table in tables:
        try:
            # Check if teamname column exists
            cursor.execute(f"PRAGMA table_info('{table}')")
            cols = [c[1] for c in cursor.fetchall()]
            if 'teamname' not in cols:
                continue
                
            print(f"Updating table {table}...")
            
            # Use LIKE to catch variants
            cursor.execute(f"UPDATE '{table}' SET teamname = 'Los Grandes' WHERE teamname LIKE 'L_S' OR teamname = 'LÃ˜S' OR teamname LIKE 'L%S' AND length(teamname) <= 4")
            updated = cursor.rowcount
            print(f"  Updated {updated} rows in {table}")
            total_updated += updated
            
        except Exception as e:
            print(f"  Error updating {table}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Done! Total rows updated: {total_updated}")

if __name__ == "__main__":
    fix_team_name()
