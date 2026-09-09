import sqlite3
import os
import sys

def sync_db_with_excel(excel_path, db_path="thanima.db"):
    if not os.path.exists(excel_path):
        print(f"Excel file not found: {excel_path}")
        return
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    import pandas as pd
    print(f"Reading valid registration numbers from '{excel_path}'...")
    df = pd.read_excel(excel_path)
    target_header = "Registration No."
    if target_header not in df.columns:
        print(f"Error: Header '{target_header}' not found in Excel. Available columns: {list(df.columns)}")
        return

    valid_regs = set(df[target_header].dropna().astype(str).str.strip().str.upper())
    print(f"Found {len(valid_regs)} valid student registration IDs in Excel file.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["entry", "sticker", "sadhya", "concert", "chendamelam"]
    
    print("\n--- TRIMMING EXTRA UNREGISTERED STUDENT RECORDS FROM DB ---")
    for t in tables:
        try:
            cursor.execute(f"SELECT count(*) FROM {t}")
            before = cursor.fetchone()[0]
            
            # Delete rows not in valid_regs UNLESS they have active live scan is_in = 1
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
    print("\nSuccessfully synced database with official Excel list!")

if __name__ == "__main__":
    excel_file = sys.argv[1] if len(sys.argv) > 1 else "registration_report_30_08_2025.xlsx"
    db_file = sys.argv[2] if len(sys.argv) > 2 else "thanima.db"
    sync_db_with_excel(excel_file, db_file)
