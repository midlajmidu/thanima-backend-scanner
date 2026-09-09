import sqlite3
import os
import sys

def restore_scans(source_db_path, target_db_path="thanima.db"):
    if not os.path.exists(source_db_path):
        print(f"Source DB file not found: {source_db_path}")
        return
    if not os.path.exists(target_db_path):
        print(f"Target DB file not found: {target_db_path}")
        return

    print(f"Restoring all active scan records (is_in=1) from '{source_db_path}' into '{target_db_path}'...")
    s_conn = sqlite3.connect(source_db_path)
    t_conn = sqlite3.connect(target_db_path)
    s_cur = s_conn.cursor()
    t_cur = t_conn.cursor()

    tables = ["entry", "sticker", "sadhya", "concert", "chendamelam"]
    for t in tables:
        try:
            s_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}';")
            if not s_cur.fetchone():
                continue

            s_cur.execute(f"PRAGMA table_info({t});")
            cols = [col[1] for col in s_cur.fetchall()]
            col_names = ", ".join(cols)
            placeholders = ", ".join(["?"] * len(cols))

            s_cur.execute(f"SELECT {col_names} FROM {t} WHERE is_in = 1;")
            rows = s_cur.fetchall()

            for r in rows:
                t_cur.execute(f"INSERT OR REPLACE INTO {t} ({col_names}) VALUES ({placeholders})", r)

            t_cur.execute(f"SELECT count(*) FROM {t} WHERE is_in = 1")
            active_cnt = t_cur.fetchone()[0]
            print(f"Table '{t:12s}': Restored {len(rows):4d} active scan records | Active is_in=1 now = {active_cnt:4d}")
        except Exception as e:
            print(f"Table '{t}' restore error: {e}")

    t_conn.commit()
    s_conn.close()
    t_conn.close()
    print("\nSuccessfully restored all active scans back to database!")

if __name__ == "__main__":
    src_db = sys.argv[1] if len(sys.argv) > 1 else "/home/adminuser/registration_backup_20260831.db"
    tgt_db = sys.argv[2] if len(sys.argv) > 2 else "thanima.db"
    restore_scans(src_db, tgt_db)
