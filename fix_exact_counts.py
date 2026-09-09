import sqlite3
import os
import sys

def fix_exact_counts(source_db_path="/home/adminuser/registration_backup_20260831.db", target_db_path="thanima.db"):
    if not os.path.exists(target_db_path):
        print(f"Target DB file not found: {target_db_path}")
        return

    print(f"Applying exact live counts to '{target_db_path}'...")
    conn = sqlite3.connect(target_db_path)
    cursor = conn.cursor()

    # 1. Master Registration List from Sadhya
    cursor.execute("SELECT registration_number FROM sadhya;")
    sadhya_regs = set(r[0] for r in cursor.fetchall() if r[0])
    print(f"Master Registration Count from Sadhya: {len(sadhya_regs)}")

    # Ensure all required tables exist
    cursor.execute("CREATE TABLE IF NOT EXISTS chendamelam (registration_number CHAR(9) PRIMARY KEY, is_in BOOLEAN DEFAULT 0, entry_time DATETIME);")

    # 2. Reset Sadhya, Concert (Informal), and Chendamelam scan counts strictly to 0
    print("1. Setting Sadhya, Informal, and Chendamelam scan counts strictly to 0...")
    cursor.execute("UPDATE sadhya SET is_in = 0, entry_time = NULL;")
    cursor.execute("UPDATE concert SET is_in = 0, last_scanned = NULL;")
    cursor.execute("UPDATE chendamelam SET is_in = 0, entry_time = NULL;")

    # 3. Restore active Sticker and Entry scans from backup source DB if available
    if os.path.exists(source_db_path):
        print(f"2. Restoring active Sticker and Entry scans from '{source_db_path}'...")
        s_conn = sqlite3.connect(source_db_path)
        s_cur = s_conn.cursor()

        for t in ["entry", "sticker"]:
            try:
                s_cur.execute(f"PRAGMA table_info({t});")
                cols = [col[1] for col in s_cur.fetchall()]
                col_names = ", ".join(cols)
                placeholders = ", ".join(["?"] * len(cols))

                s_cur.execute(f"SELECT {col_names} FROM {t} WHERE is_in = 1;")
                rows = s_cur.fetchall()
                for r in rows:
                    cursor.execute(f"INSERT OR REPLACE INTO {t} ({col_names}) VALUES ({placeholders})", r)
                print(f"  -> Restored {len(rows)} active {t} scan records.")
            except Exception as e:
                print(f"  -> Restore {t} error: {e}")
        s_conn.close()

    # 4. Align all tables with master registrations
    for reg in sadhya_regs:
        cursor.execute("INSERT OR IGNORE INTO entry (registration_number, is_in, last_scanned) VALUES (?, 0, NULL)", (reg,))
        cursor.execute("INSERT OR IGNORE INTO sticker (registration_number, is_in, entry_time) VALUES (?, 0, NULL)", (reg,))
        cursor.execute("INSERT OR IGNORE INTO concert (registration_number, is_in, last_scanned) VALUES (?, 0, NULL)", (reg,))
        cursor.execute("INSERT OR IGNORE INTO chendamelam (registration_number, is_in, entry_time) VALUES (?, 0, NULL)", (reg,))

    conn.commit()

    print("\n--- FINAL EXACT LIVE SUMMARY ---")
    for t in ["sticker & entry", "sadhya", "entry", "sticker", "concert", "chendamelam"]:
        if t == "sticker & entry":
            cursor.execute("SELECT count(*) FROM entry")
            tot = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM entry WHERE is_in = 1")
            inc = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM sticker WHERE is_in = 1")
            stc = cursor.fetchone()[0]
            print(f"Section '{t:15s}': Total={tot:4d} | In={inc:4d} | Out={max(0, tot - inc):4d} | Sticker={stc:4d}")
        else:
            cursor.execute(f"SELECT count(*) FROM {t}")
            tot = cursor.fetchone()[0]
            cursor.execute(f"SELECT count(*) FROM {t} WHERE is_in = 1")
            inc = cursor.fetchone()[0]
            print(f"Section '{t:15s}': Total={tot:4d} | In={inc:4d} | Out={max(0, tot - inc):4d}")

    conn.close()
    print("\nExact counts applied successfully!")

if __name__ == "__main__":
    src_db = sys.argv[1] if len(sys.argv) > 1 else "/home/adminuser/registration_backup_20260831.db"
    tgt_db = sys.argv[2] if len(sys.argv) > 2 else "thanima.db"
    fix_exact_counts(src_db, tgt_db)

