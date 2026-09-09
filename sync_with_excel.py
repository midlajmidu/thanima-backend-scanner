import sqlite3
import os
import sys
import glob
import csv

def find_latest_excel_file():
    search_dirs = [".", "/home/adminuser", "/tmp"]
    files = []
    for d in search_dirs:
        if os.path.exists(d):
            try:
                for ext in ["*.xlsx", "*.xls", "*.csv"]:
                    for f in glob.glob(os.path.join(d, ext)):
                        if "site-packages" not in f and "random" not in f and "numpy" not in f:
                            files.append(f)
            except Exception:
                pass
    if files:
        files.sort(key=lambda x: os.path.getmtime(x))
        latest = files[-1]
        print(f"Auto-detected latest uploaded file: '{latest}'")
        return latest
    return None

def sync_db_with_excel(excel_path=None, db_path="thanima.db"):
    if not excel_path or not os.path.exists(excel_path):
        excel_path = find_latest_excel_file()

    if not excel_path or not os.path.exists(excel_path):
        print("Error: No registration (.xlsx/.csv) file found.")
        return

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    target_header = "Registration No."
    valid_regs = set()

    print(f"Reading registration numbers from '{excel_path}'...")
    if excel_path.endswith(".csv"):
        with open(excel_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                print("Error: File is empty.")
                return
            if target_header not in headers:
                print(f"Error: Header '{target_header}' not found in CSV. Available headers: {headers}")
                return
            header_idx = headers.index(target_header)
            for row in reader:
                if len(row) > header_idx:
                    reg = str(row[header_idx]).strip().upper()
                    if reg and reg != "NAN":
                        valid_regs.add(reg)
    else:
        import pandas as pd
        df = pd.read_excel(excel_path)
        if target_header not in df.columns:
            print(f"Error: Header '{target_header}' not found in file. Available columns: {list(df.columns)}")
            return
        valid_regs = set(df[target_header].dropna().astype(str).str.strip().str.upper())

    print(f"Found {len(valid_regs)} valid student registration IDs in '{excel_path}'.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["entry", "sticker", "sadhya", "concert", "chendamelam"]

    print("\n--- TRIMMING EXTRA UNREGISTERED STUDENT RECORDS FROM DB ---")
    for t in tables:
        try:
            cursor.execute(f"SELECT count(*) FROM {t}")
            before = cursor.fetchone()[0]

            placeholders = ",".join("?" for _ in valid_regs)
            cursor.execute(f"DELETE FROM {t} WHERE registration_number NOT IN ({placeholders}) AND (is_in IS NULL OR is_in = 0)", list(valid_regs))
            deleted = cursor.rowcount

            cursor.execute(f"SELECT count(*) FROM {t}")
            after = cursor.fetchone()[0]
            print(f"Table '{t:12s}': rows before={before:4d}, removed extra={deleted:4d}, active total={after:4d}")
        except Exception as e:
            print(f"Table '{t}' error: {e}")

    conn.commit()
    conn.close()
    print("\nSuccessfully synced database with the latest uploaded file!")

if __name__ == "__main__":
    excel_file = sys.argv[1] if len(sys.argv) > 1 else None
    db_file = sys.argv[2] if len(sys.argv) > 2 else "thanima.db"
    sync_db_with_excel(excel_file, db_file)
