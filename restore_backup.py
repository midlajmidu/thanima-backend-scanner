import os
import sys
from app import app, db
from sqlalchemy.ext.serializer import loads

def restore_table_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return 0
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        with app.app_context():
            objs = loads(data, db.metadata, db.session)
            count = 0
            for obj in objs:
                db.session.merge(obj)
                count += 1
            db.session.commit()
            print(f"Successfully restored {count} records from '{filepath}' into database.")
            return count
    except Exception as e:
        print(f"Error restoring '{filepath}': {e}")
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_backup.py <path_to_table_file_or_directory>")
        sys.exit(1)

    target_path = sys.argv[1]
    if os.path.isdir(target_path):
        for fname in os.listdir(target_path):
            if fname.endswith(".table"):
                restore_table_file(os.path.join(target_path, fname))
    elif os.path.isfile(target_path):
        restore_table_file(target_path)
    else:
        dirname = os.path.dirname(target_path) or "."
        prefix = os.path.basename(target_path)
        if os.path.exists(dirname):
            found = 0
            for fname in os.listdir(dirname):
                if fname.startswith(prefix) and fname.endswith(".table"):
                    restore_table_file(os.path.join(dirname, fname))
                    found += 1
            if not found:
                print(f"No matching .table files found starting with '{target_path}'")
