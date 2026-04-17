# =====================================================================
# main.py  —  Application entry point
# =====================================================================
# CHANGES VS ORIGINAL:
#   1. Imports are flat (no models/ or utils/ subdirectories) so the app
#      runs with a simple: python main.py
#   2. Login window is fully themed using AppTheme.
#   3. open_main_menu() uses a clean nav layout with color-coded buttons.
#   4. Pressing Enter in the login form triggers login() (UX improvement).
#   5. Removed the redundant current_user_role variable — role is already
#      in scope inside open_main_menu(), so passing it directly is cleaner.
# =====================================================================

from database import initialize_database
from utils.auth import authenticate_user
from models.students import open_student_management
from models.teachers import open_teacher_management
from models.courses import open_course_management
from models.registrations import open_registration_management
from models.attendance import open_attendance_management
from utils.helpers import AppTheme, styled_button, make_header
import tkinter as tk
from tkinter import messagebox


# ─────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────

def open_main_menu(role):
    """
    Called after a successful login.

    1. Destroys the login window so it doesn't linger in the taskbar.
    2. Creates a new root Tk() window (not Toplevel — login is gone now).
    3. Builds a column of navigation buttons, label-prefixed by role.

    Parameters
    ----------
    role : str   "admin" gives full CRUD access; anything else = view only.
    """
    login_window.destroy()   # ← Remove the login screen from memory

    menu = tk.Tk()
    menu.title("School Management System")
    menu.geometry("420x540")
    menu.configure(bg=AppTheme.BG)
    menu.resizable(False, False)   # Fixed size keeps the layout tidy

    # ── Dark header banner ────────────────────────────────────────
    make_header(menu, "🎓 School Management System")

    # Role badge — green for admin, grey for regular user
    # This gives the logged-in user instant visual confirmation of
    # what they're allowed to do.
    badge_color = AppTheme.SUCCESS if role == "admin" else AppTheme.NEUTRAL
    tk.Label(
        menu,
        text=f"  Logged in as: {role.upper()}  ",
        bg=badge_color,
        fg="#FFFFFF",
        font=AppTheme.FONT_SMALL,
        pady=4,
    ).pack(fill="x")

    # ── Navigation buttons ────────────────────────────────────────
    # All buttons go in a padded frame so they don't touch the edges.
    nav_frame = tk.Frame(menu, bg=AppTheme.BG, pady=10)
    nav_frame.pack(fill="both", expand=True, padx=40)

    # Admins see "Manage ...", regular users see "View ..."
    # One line controls the label on all five buttons.
    prefix = "Manage" if role == "admin" else "View"

    # Define buttons as (label, handler) pairs.
    # This list-based approach is easy to extend — just add a tuple.
    sections = [
        (f"{prefix} Students",      lambda: open_student_management(role)),
        (f"{prefix} Teachers",      lambda: open_teacher_management(role)),
        (f"{prefix} Courses",       lambda: open_course_management(role)),
        (f"{prefix} Registrations", lambda: open_registration_management(role)),
        (f"{prefix} Attendance",    lambda: open_attendance_management(role)),
    ]

    for label, handler in sections:
        # fill="x" makes every button stretch to the same width as the frame
        btn = styled_button(nav_frame, label, handler, style="primary", width=32)
        btn.pack(pady=6, fill="x")

    # Exit button in a neutral grey so it visually reads as secondary
    styled_button(nav_frame, "Exit", menu.quit, style="neutral", width=32).pack(
        pady=(16, 6), fill="x"
    )

    menu.mainloop()


# ─────────────────────────────────────────────────────────────────────
# LOGIN LOGIC
# ─────────────────────────────────────────────────────────────────────

def login():
    """
    Reads the username and password fields, calls authenticate_user(),
    and either opens the main menu or shows an error dialog.

    .strip() removes accidental leading/trailing spaces that would
    otherwise cause "correct" credentials to fail.
    """
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    role = authenticate_user(username, password)

    if role:
        open_main_menu(role)    # Credentials valid — proceed
    else:
        messagebox.showerror(
            "Login Failed",
            "Invalid username or password.\nPlease try again.",
        )


# ─────────────────────────────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────────────────────────────

# initialize_database() checks whether school.db exists.
# If not, it creates all tables and seeds the default admin/user accounts.
# This must run before the login window appears.
initialize_database()

# ── Login window ──────────────────────────────────────────────────────
login_window = tk.Tk()
login_window.title("Login — School Management System")
login_window.geometry("360x310")
login_window.configure(bg=AppTheme.BG)
login_window.resizable(False, False)   # Login window has a fixed size

# Dark navy header band
make_header(login_window, "🎓 School MS Login")

# ── Form frame ────────────────────────────────────────────────────────
# A separate Frame keeps the form centered and padded away from the edges.
form = tk.Frame(login_window, bg=AppTheme.BG, pady=20)
form.pack(expand=True)   # expand=True vertically centers the form

# Username label + entry
tk.Label(
    form, text="Username",
    font=AppTheme.FONT_LABEL, bg=AppTheme.BG, fg=AppTheme.TEXT,
).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))

username_entry = tk.Entry(
    form,
    font=AppTheme.FONT_ENTRY,
    width=22,
    relief="flat",
    highlightthickness=1,
    highlightbackground=AppTheme.BORDER,
    highlightcolor=AppTheme.PRIMARY,   # Blue outline appears on focus
)
username_entry.grid(row=0, column=1)

# Password label + masked entry
tk.Label(
    form, text="Password",
    font=AppTheme.FONT_LABEL, bg=AppTheme.BG, fg=AppTheme.TEXT,
).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 10))

password_entry = tk.Entry(
    form,
    show="•",                          # Mask password characters with bullets
    font=AppTheme.FONT_ENTRY,
    width=22,
    relief="flat",
    highlightthickness=1,
    highlightbackground=AppTheme.BORDER,
    highlightcolor=AppTheme.PRIMARY,
)
password_entry.grid(row=1, column=1)

# Login button spans both columns, full width
login_btn = styled_button(form, "Login", login, style="primary", width=30)
login_btn.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew")

# IMPROVEMENT: pressing Enter anywhere in the login window triggers login()
# Users expect this from every login form — it was missing in the original.
login_window.bind("<Return>", lambda event: login())

login_window.mainloop()
