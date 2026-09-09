import sqlite3
import os
import sys

def deduplicate_db(db_path):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    print(f"Cleaning duplicates from '{db_path}'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    log_tables = ['entry_log', 'concert_log', 'modify_log']
    for t in log_tables:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}';")
            if not cursor.fetchone():
                continue
            cursor.execute(f"SELECT count(*) FROM {t}")
            before = cursor.fetchone()[0]

            if t == 'modify_log':
                cursor.execute('''DELETE FROM modify_log WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM modify_log GROUP BY registration_number, action, sticker, entry, sadhya, concert, chendamelam, when_modified
                )''')
            elif t in ['entry_log', 'concert_log']:
                cursor.execute(f'''DELETE FROM {t} WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM {t} GROUP BY registration_number, is_entry, time
                )''')

            cursor.execute(f"SELECT count(*) FROM {t}")
            after = cursor.fetchone()[0]
            print(f"  -> Table '{t}': rows before={before}, after deduplication={after} (removed {before - after} duplicates).")
        except Exception as e:
            print(f"  -> Table '{t}' clean error: {e}")

    conn.commit()

    # Print final counts of all tables
    print("\n--- Final Clean Database Table Summary ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
    for t in tables:
        cursor.execute(f"SELECT count(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"Table '{t}': {cnt} total rows")

    conn.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "thanima.db"
    deduplicate_db(db_file)
