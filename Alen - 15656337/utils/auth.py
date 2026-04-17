# =====================================================================
# auth.py  —  User authentication
# =====================================================================
# BUG FIXED ▶ DUPLICATE FUNCTION DEFINITION
#   The original file defined authenticate_user() TWICE.
#   Python silently overwrites a function when it is defined again in
#   the same module, so only the second (bottom) version was ever used.
#   While both versions happened to be identical in logic, having two
#   definitions is dangerous: future edits to one copy would be ignored.
#   Solution: keep exactly one clean, documented version.
# =====================================================================

from database import get_connection


def authenticate_user(username, password):
    """
    Checks whether (username, password) matches a record in the Users table.

    Parameters
    ----------
    username : str   The value typed in the username field.
    password : str   The value typed in the password field.

    Returns
    -------
    str | None
        The role string (e.g. "admin" or "user") if credentials are valid,
        or None if the username/password combination was not found.

    How it works
    ------------
    1.  Open a database connection via get_connection().
    2.  Run a SELECT with two WHERE conditions (username AND password).
        Both are passed as query parameters (?), not string-formatted
        into the SQL — this prevents SQL injection attacks.
    3.  fetchone() returns a one-element tuple like ("admin",), or None.
    4.  Always close the connection in the finally block so we don't
        leave open database handles lying around.

    Security note
    -------------
    Passwords are stored as plain text here to keep this project simple.
    In a production system you would store a bcrypt hash and verify with
    bcrypt.checkpw(password.encode(), stored_hash).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            # Parameterised query — the ? placeholders are filled safely
            # by sqlite3; the driver escapes special characters for us.
            "SELECT role FROM Users WHERE username=? AND password=?",
            (username, password),
        )
        result = cursor.fetchone()   # Returns ("admin",) or None
    except Exception as e:
        # Log the error for debugging but don't crash the application
        print(f"[auth] Database error during login: {e}")
        result = None
    finally:
        conn.close()   # Always close — even if an exception was raised

    # result[0] extracts the role string from the tuple.
    # If result is None (no match), return None to signal failure.
    return result[0] if result else None
