from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import sqlalchemy
from sqlalchemy.ext.serializer import dumps

# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from datetime import datetime
from flask_wtf.csrf import CSRFProtect


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_config_val(filename, default):
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        try:
            val = open(filepath).read().strip()
            if val:
                return val
        except Exception:
            pass
    return default

BACKUP_PATH = get_config_val("backup_path", "./")

app = Flask(__name__)
app.config["SECRET_KEY"] = get_config_val("secret", "thanima_secret_key_2026")
app.config["SQLALCHEMY_DATABASE_URI"] = get_config_val("db_url", "sqlite:///thanima.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"timeout": 30}}
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
# limiter = Limiter(get_remote_address, app=app)

@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.close()
    except Exception:
        pass



class Sadhya(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    entry_time = db.Column(db.DateTime, nullable=True)


class Sticker(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    entry_time = db.Column(db.DateTime, nullable=True)


class Entry(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class EntryLog(db.Model):
    __tablename__ = "entry_log"
    registration_number = db.Column(
        db.CHAR(9),
        # db.ForeignKey("entry.registration_number"),
        nullable=False,
        # primary_key=True,
    )
    is_entry = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, nullable=True, primary_key=True)

    # __table_args__ = (
    #     db.PrimaryKeyConstraint(
    #         registration_number,
    #         time,
    #     ),
    #


class Concert(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class ConcertLog(db.Model):
    __tablename__ = "concert_log"
    registration_number = db.Column(
        db.CHAR(9),
        # db.ForeignKey("concert.registration_number"),
        nullable=False,
        # primary_key=True,
    )
    is_entry = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, nullable=True, primary_key=True)

    # __table_args__ = (
    #     db.PrimaryKeyConstraint(
    #         registration_number,
    #         time,
    #     ),
    # )


class Chendamelam(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    entry_time = db.Column(db.DateTime, nullable=True)


class ModifyLog(db.Model):
    __tablename__ = "modify_log"
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    action = db.Column(db.VARCHAR(10))
    sticker = db.Column(db.Boolean, default=False)
    entry = db.Column(db.Boolean, default=False)
    sadhya = db.Column(db.Boolean, default=False)
    concert = db.Column(db.Boolean, default=False)
    chendamelam = db.Column(db.Boolean, default=False)
    # table = db.Column(db.VARCHAR(10), primary_key=True)
    when_modified = db.Column(db.DateTime, nullable=True, primary_key=True)


FRONTEND_TABLES = ["sticker & entry", "sadhya", "informal"]

table_map = {
    "sticker & entry": Entry,
    "chendamelam": Chendamelam,
    "sticker": Sticker,
    "entry": Entry,
    "sadhya": Sadhya,
    "concert": Concert,
    "informal": Concert,
}
log_map = {
    "sticker & entry": EntryLog,
    "entry": EntryLog,
    "concert": ConcertLog,
    "informal": ConcertLog,
}


def get_total_counts():
    try:
        return {
            "sticker": db.session.query(Sticker).count(),
            "entry": db.session.query(Entry).count(),
            "sadhya": db.session.query(Sadhya).count(),
            "concert": db.session.query(Concert).count(),
            "informal": db.session.query(Concert).count(),
            "chendamelam": db.session.query(Chendamelam).count(),
        }
    except Exception:
        db.create_all()
        return {
            "sticker": db.session.query(Sticker).count(),
            "entry": db.session.query(Entry).count(),
            "sadhya": db.session.query(Sadhya).count(),
            "concert": db.session.query(Concert).count(),
            "informal": db.session.query(Concert).count(),
            "chendamelam": db.session.query(Chendamelam).count(),
        }


# Create the database and table
with app.app_context():
    db.create_all()
    try:
        raw_conn = db.engine.raw_connection()
        cursor = raw_conn.cursor()
        cursor.execute("ALTER TABLE modify_log ADD COLUMN chendamelam BOOLEAN DEFAULT 0")
        raw_conn.commit()
    except Exception:
        pass
    TOTAL_COUNTS = get_total_counts()


# admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:260000$2icYnMEyuKf0g3bx$7b2986b75bc182114e9f35db68a4dfa901144ff8d920b3dbc4401da506838df0"

# volunteer credentials
VOLUNTEER_USERNAME = "volunteer"
VOLUNTEER_PASSWORD_HASH = "pbkdf2:sha256:260000$zmAMt0yimYwQG3Cn$405619145cd24b8bb9767b20a785fea1b38f0dcfd0c0ef634cccdf4224b37688"



def normalize_table_name(table):
    if not table:
        return None
    t = table.strip()
    if t in ["sticker", "sticker ", "sticker & entry", "sticker_entry"]:
        return "sticker & entry"
    return t


@app.route("/reset/<string:table>")
def reset(table):
    if "admin" not in session:
        return {"error": "not an admin"}, 401

    table = normalize_table_name(table)
    if not table:
        return {"error": "no table provided"}, 400

    if table not in table_map:
        return {"error": "invalid table"}, 404

    table_obj = table_map[table]

    q = db.session.query(table_obj)
    serialized_data = dumps(q.all())
    backup_file = open(BACKUP_PATH + f"{table}.table", "wb")
    backup_file.write(serialized_data)
    backup_file.close()

    for i in db.session.query(table_obj):
        i.is_in = False

    if table in log_map:
        log_obj = log_map[table]
        db.session.query(log_obj).delete()

    db.session.commit()

    return {"error": ""}, 200


@app.route("/getCount/<string:table>")
def get_count(table):
    if "logged_in" not in session:
        return {"count": "", "error": "not logged in"}

    table = normalize_table_name(table)
    if not table:
        return {"count": "", "error": "no table provided"}

    if table not in table_map:
        return {"count": "", "error": "invalid table"}

    if table == "sticker & entry":
        entry_in = db.session.query(Entry).filter(Entry.is_in == True).count()
        entry_total = db.session.query(Entry).count()
        sticker_count = db.session.query(Sticker).filter(Sticker.is_in == True).count()
        return {
            "in_count": entry_in,
            "out_count": max(0, entry_total - entry_in),
            "sticker_count": sticker_count,
            "error": "",
        }

    table_obj = table_map[table]
    in_count = db.session.query(table_obj).filter(table_obj.is_in == True).count()
    total_count = db.session.query(table_obj).count()
    return {
        "in_count": in_count,
        "out_count": max(0, total_count - in_count),
        "error": "",
    }


def get_log(reg_number, table):
    table = normalize_table_name(table) or ""
    table_obj = log_map.get(table)
    if not table_obj:
        return []
    return (
        db.session.query(table_obj)
        .filter(table_obj.registration_number == reg_number)
        .all()
    )


@app.route("/", methods=["GET", "POST"])
# @limiter.limit("200 per minute")
def index():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    log = []
    table = normalize_table_name(request.args.get("table", None))
    reg_number = ""

    if request.method == "POST":
        reg_number = request.form["registration_number"].strip().upper()

        if table == "sticker & entry":
            entry_student = Entry.query.filter_by(registration_number=reg_number).first()
            sticker_student = Sticker.query.filter_by(registration_number=reg_number).first()

            if not entry_student and not sticker_student:
                flash("Not registered", "error")
            else:
                sticker_just_added = False
                if sticker_student:
                    if not sticker_student.is_in:
                        sticker_student.is_in = True
                        sticker_student.entry_time = datetime.now()
                        sticker_just_added = True

                if entry_student:
                    entry_student.is_in = not entry_student.is_in
                    entry_student.last_scanned = datetime.now()
                    record = EntryLog(
                        registration_number=reg_number,
                        time=datetime.now(),
                        is_entry=entry_student.is_in,
                    )
                    db.session.add(record)

                db.session.commit()
                log = get_log(reg_number, "entry")

                if entry_student and entry_student.is_in:
                    if sticker_just_added:
                        flash("Sticker issued & Entered", "success")
                    else:
                        flash("Entered", "success")
                else:
                    flash("Left", "error")
        else:
            table_obj = table_map.get(table) if table else None

            if not table_obj:
                flash("Invalid category selected", "error")
            else:
                student = table_obj.query.filter_by(registration_number=reg_number).first()

                if not student:
                    flash("Not registered", "error")
                else:
                    if table in ["sadhya", "sticker", "chendamelam"]:
                        if student.is_in:
                            entry_time_str = f" at {student.entry_time.strftime('%H:%M:%S')}" if student.entry_time else ""
                            flash(
                                f"Already scanned{entry_time_str}",
                                "error",
                            )
                        else:
                            student.is_in = True
                            student.entry_time = datetime.now()
                            db.session.commit()
                            flash("Successfully scanned.", "success")
                    else:
                        student.is_in = not student.is_in
                        log_cls = log_map.get(table, EntryLog)
                        record = log_cls(
                            registration_number=reg_number, time=datetime.now()
                        )

                        if not student.is_in:
                            record.is_entry = False
                        else:
                            record.is_entry = True

                        student.last_scanned = datetime.now()
                        db.session.add(record)
                        db.session.commit()

                        log = get_log(reg_number, table)

    count_response = get_count(table=table) if table else {"error": "no table provided"}

    if count_response.get("error"):
        in_count = ""
        out_count = ""
        sticker_count = ""
    else:
        in_count = count_response.get("in_count", "")
        out_count = count_response.get("out_count", "")
        sticker_count = count_response.get("sticker_count", "")

    db.session.expunge_all()
    for i, r in enumerate(log):
        if r.time and hasattr(r.time, "strftime"):
            log[i].time = r.time.strftime("%H:%M:%S")

    return render_template(
        "index.html",
        tables=FRONTEND_TABLES,
        table=table,
        in_count=in_count,
        out_count=out_count,
        sticker_count=sticker_count,
        log=log[::-1],
        reg_no=reg_number,
    )


@app.route("/verify", methods=["GET", "POST"])
# @limiter.limit("200 per minute")
def verify():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    log = []
    table = normalize_table_name(request.args.get("table", None))
    reg_number = ""

    if request.method == "POST":
        reg_number = request.form["registration_number"].strip().upper()

        if table == "sticker & entry":
            entry_student = Entry.query.filter_by(registration_number=reg_number).first()
            sticker_student = Sticker.query.filter_by(registration_number=reg_number).first()

            if not entry_student and not sticker_student:
                flash("Not registered", "error")
            else:
                flash("Registered", "success")

                scanned_time = None
                if entry_student and entry_student.last_scanned:
                    scanned_time = entry_student.last_scanned
                elif sticker_student and sticker_student.entry_time:
                    scanned_time = sticker_student.entry_time

                is_scanned = (
                    (entry_student and (entry_student.is_in or entry_student.last_scanned is not None))
                    or (sticker_student and sticker_student.is_in)
                )

                if is_scanned:
                    time_str = (
                        f" at {scanned_time.strftime('%H:%M:%S')}"
                        if (scanned_time and hasattr(scanned_time, "strftime"))
                        else ""
                    )
                    flash(f"Already scanned{time_str}", "error")
                else:
                    flash("Not scanned yet.", "success")

                log = get_log(reg_number, "entry")
        else:
            table_obj = table_map.get(table) if table else None

            if not table_obj:
                flash("Invalid category selected", "error")
            else:
                student = table_obj.query.filter_by(registration_number=reg_number).first()

                if not student:
                    flash("Not registered", "error")
                else:
                    flash("Registered", "success")

                    scanned_time = getattr(student, "entry_time", None) or getattr(student, "last_scanned", None)
                    is_scanned = bool(student.is_in or (scanned_time is not None))

                    if is_scanned:
                        time_str = (
                            f" at {scanned_time.strftime('%H:%M:%S')}"
                            if (scanned_time and hasattr(scanned_time, "strftime"))
                            else ""
                        )
                        flash(f"Already scanned{time_str}", "error")
                    else:
                        flash("Not scanned yet.", "success")

                    log = get_log(reg_number, table)

    db.session.expunge_all()
    for i, r in enumerate(log):
        if r.time and hasattr(r.time, "strftime"):
            log[i].time = r.time.strftime("%H:%M:%S")

    return render_template(
        "verify.html",
        tables=FRONTEND_TABLES,
        table=table,
        log=log[::-1],
        reg_no=reg_number,
    )


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "admin" not in session:
        flash("Admin access required", "error")
        return redirect(url_for("index"))

    success_responses, failure_responses = [], []
    reg_no = ""
    if request.method == "POST":
        reg_no = request.form["registration_number"].strip().upper()
        action = request.form.get("action", "add")

        modify_record = ModifyLog(
            registration_number=reg_no,
            action=action,
            when_modified=datetime.now(),
        )

        form_keys = request.form.keys()
        targets = []
        if "sticker_entry" in form_keys or "sticker & entry" in form_keys:
            targets.append(("sticker", Sticker))
            targets.append(("entry", Entry))
        if "sadhya" in form_keys:
            targets.append(("sadhya", Sadhya))
        if "concert" in form_keys or "informal" in form_keys:
            targets.append(("informal", Concert))
        if "chendamelam" in form_keys:
            targets.append(("chendamelam", Chendamelam))

        st_en_succ = False
        st_en_fail = False

        for name, table_obj in targets:
            record = table_obj.query.filter_by(registration_number=reg_no)
            if action == "remove":
                if record.count() > 0:
                    record.delete()
                    setattr(modify_record, name, True)
                    if name in ["sticker", "entry"]:
                        st_en_succ = True
                    else:
                        success_responses.append(f"Successfully removed from '{name.capitalize()}'")
                else:
                    if name in ["sticker", "entry"]:
                        st_en_fail = True
                    else:
                        failure_responses.append(f"Was not in '{name.capitalize()}'")
            else:
                if record.count() == 0:
                    new_record = table_obj(registration_number=reg_no)
                    db.session.add(new_record)
                    setattr(modify_record, name, True)
                    if name in ["sticker", "entry"]:
                        st_en_succ = True
                    else:
                        success_responses.append(f"Successfully added to '{name.capitalize()}'")
                else:
                    if name in ["sticker", "entry"]:
                        st_en_fail = True
                    else:
                        failure_responses.append(f"Already in '{name.capitalize()}'")

        if st_en_succ:
            act_text = "removed from" if action == "remove" else "added to"
            success_responses.append(f"Successfully {act_text} 'Sticker & Entry'")
        elif st_en_fail:
            act_text = "Was not in" if action == "remove" else "Already in"
            failure_responses.append(f"{act_text} 'Sticker & Entry'")

        if any(
            (
                modify_record.sticker,
                modify_record.entry,
                modify_record.sadhya,
                modify_record.concert,
                modify_record.chendamelam,
            )
        ):
            db.session.add(modify_record)
        db.session.commit()

    global TOTAL_COUNTS
    TOTAL_COUNTS = get_total_counts()

    return render_template(
        "edit.html",
        reg_no=reg_no,
        success_responses=success_responses,
        failure_responses=failure_responses,
    )


@app.route("/modifications", methods=["GET", "POST"])
@app.route("/modification", methods=["GET", "POST"])
def modifications():
    if "admin" not in session:
        flash("Admin access required", "error")
        return redirect(url_for("index"))

    log = db.session.query(ModifyLog).all()

    return render_template("modifications.html", log=log)


import tempfile

def process_registration_file(filepath):
    table_names = ["entry", "concert", "sadhya", "sticker", "chendamelam"]
    target_header = "Registration No."
    
    if filepath.endswith(".xlsx") or filepath.endswith(".xls"):
        import pandas as pd
        df = pd.read_excel(filepath)
        headers = list(df.columns)
        if target_header not in headers:
            raise ValueError(f"Header '{target_header}' not found in file. Available columns: {headers}")
        header_index = headers.index(target_header)
        rows = df.astype(str).values.tolist()
    else:
        import csv
        with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)
            if target_header not in headers:
                raise ValueError(f"Header '{target_header}' not found in file. Available columns: {headers}")
            header_index = headers.index(target_header)
            rows = list(csv_reader)

    db.create_all()
    raw_conn = db.engine.raw_connection()
    cursor = raw_conn.cursor()

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

    added_count = 0
    processed_regs = set()
    for row in rows:
        if len(row) <= header_index:
            continue
        reg_no = str(row[header_index]).strip().upper()
        if not reg_no or reg_no == "NAN" or reg_no in processed_regs:
            continue
        processed_regs.add(reg_no)
        
        for table_name in table_names:
            try:
                cursor.execute(
                    f"INSERT OR IGNORE INTO {table_name} (registration_number) VALUES ('{reg_no}')"
                )
            except Exception as e:
                print(f"Error inserting {reg_no} in {table_name}: {e}")
        added_count += 1

    raw_conn.commit()
    raw_conn.close()
    return added_count


@app.route("/add", methods=["GET", "POST"])
def add():
    if "admin" not in session:
        flash("Admin access required to upload registration lists", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(url_for("add"))

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("add"))

        if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
            flash("Invalid file format. Please upload a .csv or .xlsx Excel file.", "error")
            return redirect(url_for("add"))

        try:
            filename = file.filename
            ext = os.path.splitext(filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            count = process_registration_file(tmp_path)
            os.remove(tmp_path)

            global TOTAL_COUNTS
            TOTAL_COUNTS = get_total_counts()

            flash(f"Successfully processed '{filename}'! Imported/synced {count} registration records.", "success")
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "error")

    return render_template("add.html")


@app.route("/login", methods=["GET", "POST"])
# @limiter.limit("20 per minute")
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == VOLUNTEER_USERNAME and check_password_hash(
            VOLUNTEER_PASSWORD_HASH, password
        ):
            session["logged_in"] = True
            flash("Logged in as volunteer", "success")
            return redirect(url_for("index"))
        elif username == ADMIN_USERNAME and check_password_hash(
            ADMIN_PASSWORD_HASH, password
        ):
            session["logged_in"] = True
            session["admin"] = True
            flash("Logged in as admin", "success")
            return redirect(url_for("edit"))
        else:
            flash("Invalid login credentials", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("admin", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(get_config_val("port", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)



