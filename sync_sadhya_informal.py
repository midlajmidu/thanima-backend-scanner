import sqlite3
import os
import sys
import shutil
from datetime import datetime

def sync_sadhya_informal(excel_path, db_path="thanima.db"):
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found!")
        return

    if not os.path.exists(excel_path):
        print(f"Error: Excel/CSV file '{excel_path}' not found!")
        return

    # 1. Create a timestamped safety backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"thanima_backup_before_sadhya_{timestamp}.db"
    shutil.copyfile(db_path, backup_file)
    print(f"1. Created safety backup of database: '{backup_file}'")

    # 2. Extract registration numbers from Excel / CSV file
    print(f"2. Reading registration numbers from '{excel_path}'...")
    regs = set()
    
    if excel_path.endswith(".xlsx") or excel_path.endswith(".xls"):
        import pandas as pd
        df = pd.read_excel(excel_path)
        col = "Registration No." if "Registration No." in df.columns else df.columns[0]
        for val in df[col].dropna():
            cleaned = str(val).strip().upper()
            if cleaned and cleaned != "NAN":
                regs.add(cleaned)
    else:
        import csv
        with open(excel_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            idx = 0
            if header and "Registration No." in header:
                idx = header.index("Registration No.")
            for row in reader:
                if len(row) > idx:
                    cleaned = str(row[idx]).strip().upper()
                    if cleaned and cleaned != "NAN":
                        regs.add(cleaned)

    print(f"Found {len(regs)} unique registration numbers in Excel file.")

    if not regs:
        print("No valid registration numbers found. Aborting update.")
        return

    # 3. Update ONLY sadhya and concert (informal) tables
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS sadhya (registration_number CHAR(9) PRIMARY KEY, is_in BOOLEAN DEFAULT 0, entry_time DATETIME);")
    cur.execute("CREATE TABLE IF NOT EXISTS concert (registration_number CHAR(9) PRIMARY KEY, is_in BOOLEAN DEFAULT 0, last_scanned DATETIME);")

    # Reset sadhya and concert tables for new master list
    cur.execute("DELETE FROM sadhya;")
    cur.execute("DELETE FROM concert;")

    for r in regs:
        cur.execute("INSERT INTO sadhya (registration_number, is_in, entry_time) VALUES (?, 0, NULL);", (r,))
        cur.execute("INSERT INTO concert (registration_number, is_in, last_scanned) VALUES (?, 0, NULL);", (r,))

    conn.commit()

    print("\n=== SUCCESS: SADHYA & INFORMAL TABLES UPDATED ===")
    cur.execute("SELECT count(*), sum(case when is_in=1 then 1 else 0 end) FROM sadhya;")
    s_tot, s_in = cur.fetchone()
    cur.execute("SELECT count(*), sum(case when is_in=1 then 1 else 0 end) FROM concert;")
    c_tot, c_in = cur.fetchone()
    cur.execute("SELECT count(*), sum(case when is_in=1 then 1 else 0 end) FROM entry;")
    e_tot, e_in = cur.fetchone()
    cur.execute("SELECT count(*), sum(case when is_in=1 then 1 else 0 end) FROM sticker;")
    st_tot, st_in = cur.fetchone()

    print(f"Sadhya Table          -> Total: {s_tot} | In: {s_in or 0} | Out: {s_tot - (s_in or 0)}")
    print(f"Informal Table        -> Total: {c_tot} | In: {c_in or 0} | Out: {c_tot - (c_in or 0)}")
    print(f"Sticker & Entry (Live)-> Total: {e_tot} | In: {e_in or 0} | Out: {e_tot - (e_in or 0)} | Sticker: {st_in or 0}")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sync_sadhya_informal.py <path_to_excel_or_csv> [target_db_path]")
    else:
        excel_file = sys.argv[1]
        target_db = sys.argv[2] if len(sys.argv) > 2 else "thanima.db"
        sync_sadhya_informal(excel_file, target_db)
