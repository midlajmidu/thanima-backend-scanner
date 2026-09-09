import sqlite3
import os
import sys

def align_entry_to_sadhya(db_path="thanima.db"):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    print(f"Aligning all tables strictly with Sadhya master list in '{db_path}'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get valid registration numbers from Sadhya table
    cursor.execute("SELECT registration_number FROM sadhya;")
    sadhya_regs = set(r[0] for r in cursor.fetchall() if r[0])
    print(f"Sadhya Master Registration Count: {len(sadhya_regs)}")

    tables = ["entry", "sticker", "concert"]
    placeholders = ",".join("?" for _ in sadhya_regs)

    # 1. Delete all rows in entry/sticker/concert that are NOT in sadhya_regs
    for t in tables:
        try:
            cursor.execute(f"SELECT count(*) FROM {t}")
            before = cursor.fetchone()[0]

            cursor.execute(f"DELETE FROM {t} WHERE registration_number NOT IN ({placeholders})", list(sadhya_regs))
            removed = cursor.rowcount

            cursor.execute(f"SELECT count(*) FROM {t}")
            total = cursor.fetchone()[0]
            print(f"Table '{t:12s}': Before={before:4d} | Removed Invalid/Old Backup={removed:4d} | Filtered={total:4d}")
        except Exception as e:
            print(f"Table '{t}' delete error: {e}")

    # 2. Ensure every Sadhya reg exists in entry, sticker, concert
    for reg in sadhya_regs:
        cursor.execute("INSERT OR IGNORE INTO entry (registration_number, is_in, last_scanned) VALUES (?, 0, NULL)", (reg,))
        cursor.execute("INSERT OR IGNORE INTO sticker (registration_number, is_in, entry_time) VALUES (?, 0, NULL)", (reg,))
        cursor.execute("INSERT OR IGNORE INTO concert (registration_number, is_in, last_scanned) VALUES (?, 0, NULL)", (reg,))

    conn.commit()

    print("\n--- FINAL ALIGNED LIVE SUMMARY ---")
    for t in ["sticker & entry", "sadhya", "entry", "sticker", "concert"]:
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
    print("\nSuccessfully aligned all section counts to Sadhya master total!")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "thanima.db"
    align_entry_to_sadhya(db_file)
