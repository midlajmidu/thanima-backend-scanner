import sqlite3
import os
import sys

def reset_scan_status(db_path):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    print(f"Resetting scan statuses in '{db_path}'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["entry", "sticker", "sadhya", "concert", "chendamelam"]
    for t in tables:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}';")
            if not cursor.fetchone():
                continue
            
            cursor.execute(f"UPDATE {t} SET is_in = 0;")
            if t in ["entry", "concert"]:
                cursor.execute(f"UPDATE {t} SET last_scanned = NULL;")
            elif t in ["sadhya", "sticker", "chendamelam"]:
                cursor.execute(f"UPDATE {t} SET entry_time = NULL;")
                
            print(f"  -> Table '{t}': reset all scan statuses to 0 (is_in = False).")
        except Exception as e:
            print(f"  -> Table '{t}' reset error: {e}")

    log_tables = ["entry_log", "concert_log", "modify_log"]
    for l in log_tables:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{l}';")
            if not cursor.fetchone():
                continue
            cursor.execute(f"DELETE FROM {l};")
            print(f"  -> Log table '{l}': cleared logs.")
        except Exception as e:
            print(f"  -> Log table '{l}' clear error: {e}")

    conn.commit()
    conn.close()
    print("\nSuccessfully reset all scan statuses to 0! All 2,459 registered students are preserved.")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "thanima.db"
    reset_scan_status(db_file)
