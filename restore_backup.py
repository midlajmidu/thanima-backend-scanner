import os
import sys
import sqlite3

def restore_table_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return 0
    try:
        from app import app, db
        from sqlalchemy.ext.serializer import loads
        with open(filepath, "rb") as f:
            data = f.read()
        with app.app_context():
            objs = loads(data, db.metadata, db.session)
            count = 0
            for obj in objs:
                db.session.merge(obj)
                count += 1
            db.session.commit()
            print(f"Successfully restored {count} records from '{filepath}' into active database.")
            return count
    except Exception as e:
        print(f"Error restoring table file '{filepath}': {e}")
        return 0

def restore_db_file(source_db_path, target_db_path=None):
    if not target_db_path:
        # Check standard db names in directory
        for candidate in ["thanima.db", "registration.db"]:
            if os.path.exists(candidate):
                target_db_path = candidate
                break
        if not target_db_path:
            target_db_path = "thanima.db"

    if not os.path.exists(source_db_path):
        print(f"Source DB file not found: {source_db_path}")
        return 0

    print(f"Merging records from '{source_db_path}' into '{target_db_path}'...")
    try:
        s_conn = sqlite3.connect(source_db_path)
        t_conn = sqlite3.connect(target_db_path)
        s_cur = s_conn.cursor()
        t_cur = t_conn.cursor()

        s_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in s_cur.fetchall()]

        total_merged = 0
        for t in tables:
            if t in ["sqlite_sequence"]:
                continue
            try:
                s_cur.execute(f"PRAGMA table_info({t});")
                cols = [col[1] for col in s_cur.fetchall()]
                col_names = ", ".join(cols)
                placeholders = ", ".join(["?"] * len(cols))

                s_cur.execute(f"SELECT {col_names} FROM {t};")
                rows = s_cur.fetchall()

                t_cur.executemany(f"INSERT OR IGNORE INTO {t} ({col_names}) VALUES ({placeholders})", rows)
                total_merged += len(rows)
                print(f"  -> Table '{t}': processed {len(rows)} records.")
            except Exception as e:
                print(f"  -> Table '{t}' merge error: {e}")

        t_conn.commit()
        s_conn.close()
        t_conn.close()
        print(f"Done! Merged {total_merged} total rows from '{source_db_path}' into '{target_db_path}'.")
        return total_merged
    except Exception as e:
        print(f"Error merging DB file '{source_db_path}': {e}")
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_backup.py <path_to_table_file_or_db_or_directory>")
        sys.exit(1)

    target_path = sys.argv[1]

    if target_path.endswith(".db"):
        restore_db_file(target_path)
    elif os.path.isdir(target_path):
        for fname in os.listdir(target_path):
            if fname.endswith(".table"):
                restore_table_file(os.path.join(target_path, fname))
            elif fname.endswith(".db"):
                restore_db_file(os.path.join(target_path, fname))
    elif os.path.isfile(target_path):
        if target_path.endswith(".table"):
            restore_table_file(target_path)
        else:
            restore_db_file(target_path)
    else:
        dirname = os.path.dirname(target_path) or "."
        prefix = os.path.basename(target_path)
        if os.path.exists(dirname):
            found = 0
            for fname in os.listdir(dirname):
                if fname.startswith(prefix) and fname.endswith(".table"):
                    restore_table_file(os.path.join(dirname, fname))
                    found += 1
                elif fname.startswith(prefix) and fname.endswith(".db"):
                    restore_db_file(os.path.join(dirname, fname))
                    found += 1
            if not found:
                print(f"No matching files found for '{target_path}'")
