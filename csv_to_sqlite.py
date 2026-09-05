import csv
import sqlite3
from sys import argv


def csv_to_sqlite(csv_file, db_file):
    table_names = ["entry", "concert", "sadhya", "sticker", "chendamelam"]

    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    target_header = "Registration No."

    # Read the file (CSV or Excel)
    if csv_file.endswith(".xlsx") or csv_file.endswith(".xls"):
        import pandas as pd
        df = pd.read_excel(csv_file)
        headers = list(df.columns)
        header_index = headers.index(target_header)
        rows = df.astype(str).values.tolist()
    else:
        with open(csv_file, "r") as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)
            header_index = headers.index(target_header)
            rows = list(csv_reader)

    # Create tables (preserve existing tables and scan records if they exist)
    for table_name in table_names:
        if table_name in ["entry", "concert"]:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
                "registration_number CHAR(9) NOT NULL PRIMARY KEY,\n"
                "is_in BOOLEAN DEFAULT FALSE,\n"
                "last_scanned DATETIME);"
            )
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name}_log (\n"
                "registration_number CHAR(9),\n"
                "is_entry BOOLEAN,\n"
                "time DATETIME,\n"
                "PRIMARY KEY(registration_number, time));"
            )
        elif table_name in ["sadhya", "sticker", "chendamelam"]:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
                "registration_number CHAR(9) NOT NULL PRIMARY KEY,\n"
                "is_in BOOLEAN DEFAULT FALSE,\n"
                "entry_time DATETIME);"
            )

    # Insert data (INSERT OR IGNORE keeps existing participants and their scan status intact)
    for row in rows:
        reg_no = str(row[header_index]).strip()
        if not reg_no or reg_no.lower() == "nan":
            continue
        for table_name in table_names:
            try:
                cursor.execute(
                    f"INSERT OR IGNORE INTO {table_name} (registration_number) VALUES ('{reg_no.upper()}')"
                )
            except sqlite3.IntegrityError as e:
                print(f"Got {e} due to {reg_no}, continuing")

    conn.commit()
    conn.close()

    print(
        f"Data from {csv_file} has been successfully imported to {db_file} in tables {table_names}."
    )


if __name__ == "__main__":
    db_file = argv[2]

    csv_file = argv[1]

    csv_to_sqlite(csv_file, db_file)
