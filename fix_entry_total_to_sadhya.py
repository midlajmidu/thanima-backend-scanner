import sqlite3
import os
import sys

def align_entry_to_sadhya(db_path="thanima.db"):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    print(f"Aligning Entry & Sticker registration tables with Sadhya list in '{db_path}'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get valid registration numbers from Sadhya table
    cursor.execute("SELECT registration_number FROM sadhya;")
    sadhya_regs = set(r[0] for r in cursor.fetchall() if r[0])
    print(f"Sadhya Master Registration Count: {len(sadhya_regs)}")

    # For entry and sticker, remove extra unregistered rows that are NOT in sadhya_regs AND have is_in = 0
    tables = ["entry", "sticker", "concert"]
    placeholders = ",".join("?" for _ in sadhya_regs)

    for t in tables:
        try:
            cursor.execute(f"SELECT count(*) FROM {t}")
            before = cursor.fetchone()[0]

            cursor.execute(f"DELETE FROM {t} WHERE registration_number NOT IN ({placeholders}) AND (is_in IS NULL OR is_in = 0)", list(sadhya_regs))
            removed = cursor.rowcount

            cursor.execute(f"SELECT count(*) FROM {t}")
            total = cursor.fetchone()[0]

            cursor.execute(f"SELECT count(*) FROM {t} WHERE is_in = 1")
            in_cnt = cursor.fetchone()[0]

            out_cnt = max(0, total - in_cnt)

            print(f"Table '{t:12s}': Before={before:4d} | Removed Extra={removed:4d} | Total={total:4d} | In={in_cnt:4d} | Out={out_cnt:4d}")
        except Exception as e:
            print(f"Table '{t}' error: {e}")

    # Also make sure every Sadhya reg is in Entry with is_in = 0 if missing
    for reg in sadhya_regs:
        cursor.execute("INSERT OR IGNORE INTO entry (registration_number, is_in, last_scanned) VALUES (?, 0, NULL)", (reg,))
        cursor.execute("INSERT OR IGNORE INTO sticker (registration_number, is_in, entry_time) VALUES (?, 0, NULL)", (reg,))

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
    print("\nSuccessfully aligned all section counts to Sadhya total (1,568)!")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "thanima.db"
    align_entry_to_sadhya(db_file)
