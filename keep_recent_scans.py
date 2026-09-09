import sqlite3
import os
import sys

def filter_real_scans(db_path, cutoff_date="2026-09-01"):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    print(f"Analyzing scan timestamps in '{db_path}' with cutoff '{cutoff_date}'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables_datetime_col = {
        "sticker": "entry_time",
        "sadhya": "entry_time",
        "chendamelam": "entry_time",
        "entry": "last_scanned",
        "concert": "last_scanned",
    }

    print("\n--- TIMESTAMP ANALYSIS BEFORE CLEANUP ---")
    for table, col in tables_datetime_col.items():
        try:
            cursor.execute(f"SELECT count(*) FROM {table} WHERE {col} IS NOT NULL AND {col} >= '{cutoff_date}'")
            recent = cursor.fetchone()[0]
            cursor.execute(f"SELECT count(*) FROM {table} WHERE {col} IS NOT NULL AND {col} < '{cutoff_date}'")
            old = cursor.fetchone()[0]
            cursor.execute(f"SELECT count(*) FROM {table} WHERE is_in = 1")
            total_in = cursor.fetchone()[0]
            print(f"Table '{table:12s}': Total is_in=True: {total_in:4d} | Real Live Scans (>= {cutoff_date}): {recent:4d} | Old Backup Scans (< {cutoff_date}): {old:4d}")
        except Exception as e:
            print(f"Table '{table}' error: {e}")

    # Reset old backup scan statuses where timestamp < cutoff_date
    print("\n--- REMOVING OLD BACKUP SCANS & KEEPING LIVE SCANS ---")
    for table, col in tables_datetime_col.items():
        try:
            # Set is_in = 0 for old backup scans
            cursor.execute(f"UPDATE {table} SET is_in = 0, {col} = NULL WHERE {col} IS NOT NULL AND {col} < '{cutoff_date}'")
            reset_count = cursor.rowcount
            print(f"  -> Table '{table}': Reset {reset_count} old backup scan records to is_in = 0.")
        except Exception as e:
            print(f"  -> Table '{table}' update error: {e}")

    # Remove old log entries from log tables
    log_tables = ["entry_log", "concert_log"]
    for l in log_tables:
        try:
            cursor.execute(f"DELETE FROM {l} WHERE time IS NOT NULL AND time < '{cutoff_date}'")
            deleted_logs = cursor.rowcount
            print(f"  -> Log table '{l}': Removed {deleted_logs} old backup logs.")
        except Exception as e:
            print(f"  -> Log table '{l}' delete error: {e}")

    conn.commit()

    print("\n--- FINAL LIVE SCAN COUNTS AFTER CLEANUP ---")
    for table in tables_datetime_col.keys():
        cursor.execute(f"SELECT count(*) FROM {table} WHERE is_in = 1")
        live_in = cursor.fetchone()[0]
        cursor.execute(f"SELECT count(*) FROM {table}")
        total_reg = cursor.fetchone()[0]
        print(f"Table '{table:12s}': Registered={total_reg:4d} | Active Live Scans (is_in=1): {live_in:4d}")

    conn.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "thanima.db"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2026-09-01"
    filter_real_scans(db_file, cutoff)
