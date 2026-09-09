import sqlite3
import os
import sys

def restore_unscanned_registrations(source_db_path, target_db_path="thanima.db"):
    if not os.path.exists(source_db_path):
        print(f"Source DB file not found: {source_db_path}")
        return
    if not os.path.exists(target_db_path):
        print(f"Target DB file not found: {target_db_path}")
        return

    print(f"Adding registered student IDs from '{source_db_path}' into '{target_db_path}'...")
    s_conn = sqlite3.connect(source_db_path)
    t_conn = sqlite3.connect(target_db_path)
    s_cur = s_conn.cursor()
    t_cur = t_conn.cursor()

    tables = ["entry", "sticker", "sadhya", "concert", "chendamelam"]
    
    for t in tables:
        try:
            s_cur.execute(f"SELECT registration_number FROM {t};")
            s_regs = [r[0] for r in s_cur.fetchall() if r[0]]

            added_count = 0
            for reg in s_regs:
                # Insert if not exists with is_in = 0
                if t in ["entry", "concert"]:
                    t_cur.execute(f"INSERT OR IGNORE INTO {t} (registration_number, is_in, last_scanned) VALUES (?, 0, NULL)", (reg,))
                else:
                    t_cur.execute(f"INSERT OR IGNORE INTO {t} (registration_number, is_in, entry_time) VALUES (?, 0, NULL)", (reg,))
                if t_cur.rowcount > 0:
                    added_count += 1

            t_cur.execute(f"SELECT count(*) FROM {t}")
            total = t_cur.fetchone()[0]
            t_cur.execute(f"SELECT count(*) FROM {t} WHERE is_in = 1")
            in_cnt = t_cur.fetchone()[0]

            print(f"Table '{t:12s}': Added {added_count:4d} unscanned registrations | Total={total:4d} | is_in=True={in_cnt:4d} | Out={max(0, total - in_cnt):4d}")
        except Exception as e:
            print(f"Table '{t}' error: {e}")

    t_conn.commit()
    s_conn.close()
    t_conn.close()
    print("\nDone! All student registrations loaded with accurate In/Out counts!")

if __name__ == "__main__":
    source_db = sys.argv[1] if len(sys.argv) > 1 else "/home/adminuser/registration_backup_20260831.db"
    target_db = sys.argv[2] if len(sys.argv) > 2 else "thanima.db"
    restore_unscanned_registrations(source_db, target_db)
