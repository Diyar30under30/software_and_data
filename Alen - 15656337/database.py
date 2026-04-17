# =====================================================================
# database.py  —  SQLite connection and initialization
# =====================================================================
# No logic changes from the original — this file was already correct.
# Added documentation comments explaining each step.
# =====================================================================

import sqlite3
import os

# Always resolve school.db relative to this file's own directory,
# so the app works no matter what the current working directory is.
_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DIR, "school.db")
SQL_PATH = os.path.join(_DIR, "school_db.sql")


def get_connection():
    """
    Opens and returns a connection to the SQLite database file.

    SQLite stores the entire database in a single file (school.db).
    sqlite3.connect() creates the file if it doesn't exist yet, but
    initialize_database() handles first-run table creation separately.

    Returns
    -------
    sqlite3.Connection
        Always call conn.close() when done, or use a context manager.
    """
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """
    One-time setup: creates all tables from school_db.sql and seeds
    default admin and user accounts.

    The os.path.exists() check means this is safe to call every time
    the app starts — it simply skips initialization if the DB is there.

    Depends on school_db.sql being present in the same directory.
    """
    if not os.path.exists("school.db"):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Read and execute the full SQL schema script
            with open("school_db.sql", "r") as f:
                sql_script = f.read()
                # executescript() runs multiple statements separated by semicolons
                cursor.executescript(sql_script)

            # Seed a default admin account if none exists
            cursor.execute("SELECT COUNT(*) FROM Users WHERE username='admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO Users (username, password, role) VALUES (?, ?, ?)",
                    ("admin", "diyar123", "admin"),
                )

            # Seed a default regular user account if none exists
            cursor.execute("SELECT COUNT(*) FROM Users WHERE username='user'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO Users (username, password, role) VALUES (?, ?, ?)",
                    ("user", "user123", "user"),
                )

            conn.commit()
            print("✅ Database initialized using school_db.sql.")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
        finally:
            conn.close()
    else:
        print("✅ Database already exists — initialization skipped.")
