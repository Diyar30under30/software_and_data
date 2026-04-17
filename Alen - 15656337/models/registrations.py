# =====================================================================
# registrations.py  —  Registration CRUD + filter
# =====================================================================
# BUG FIXED ▶ UPDATE FAILS AFTER SELECTING A ROW
#
#   Root cause:
#       The Treeview shows (ID, StudentName, CourseName, Date).
#       The student and course combos are populated as "1 - John Smith"
#       and "2 - Mathematics" so extract_id() can split on " - " to
#       get the numeric ID.
#
#       But autofill_fields() was doing:
#           student_combo.set(f"{item[1]}")   # "John Smith"  ← no ID prefix
#           course_combo.set(f"{item[2]}")    # "Mathematics" ← no ID prefix
#
#       So after clicking a row and pressing Update, extract_id() tried:
#           int("John Smith".split(" - ")[0])   →  int("John Smith")
#           ↑  ValueError crash — the update silently did nothing.
#
#   Fix:
#       When autofilling, look up the student/course ID from the database
#       using the name stored in the Treeview row, then set the combo to
#       the full "ID - Name" format that extract_id() expects.
#
# OTHER CHANGES:
#   1. AppTheme + styled_button() for visual consistency.
#   2. apply_treeview_style() for themed table headers.
#   3. PlaceholderEntry imported from utils.helpers.
#   4. Status bar for user feedback.
# =====================================================================

from database import get_connection
from utils.helpers import (
    AppTheme, PlaceholderEntry, apply_treeview_style,
    make_window, make_header, styled_button,
)
from tkinter import messagebox, ttk
import sqlite3
import tkinter as tk


# ─────────────────────────────────────────────────────────────────────
# DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────────────

def add_registration(student_id, course_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Registrations (student_id, course_id) VALUES (?, ?)",
            (student_id, course_id),
        )
        conn.commit()
        messagebox.showinfo("Success", "Registration added.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def update_registration(reg_id, student_id, course_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Registrations SET student_id=?, course_id=? WHERE id=?",
            (student_id, course_id, reg_id),
        )
        conn.commit()
        messagebox.showinfo("Updated", "Registration updated.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def view_registrations(tree):
    """
    Fetches registrations with JOINed student and course names.
    The Treeview shows human-readable names, not raw foreign key IDs.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT r.id, "
        "       s.first_name || ' ' || s.last_name AS student, "
        "       c.name AS course, "
        "       r.registration_date "
        "FROM Registrations r "
        "JOIN Students s ON r.student_id = s.id "
        "JOIN Courses  c ON r.course_id  = c.id"
    )
    rows = cursor.fetchall()
    conn.close()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)


def delete_registration(reg_id, tree):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Registrations WHERE id=?", (reg_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Registration deleted.")
        view_registrations(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────

def open_registration_management(current_user_role):

    rm = make_window("Registration Management", width=680, height=520)
    make_header(rm, "📋 Registration Management")

    # ── Populate dropdown data ────────────────────────────────────
    # Load students and courses once when the window opens.
    # Store as dicts for fast lookup in autofill (see bug fix below).
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name || ' ' || last_name FROM Students")
    students = cursor.fetchall()       # [(1, "John Smith"), (2, "Jane Doe"), ...]
    cursor.execute("SELECT id, name FROM Courses")
    courses = cursor.fetchall()        # [(1, "Math"), (2, "Science"), ...]
    conn.close()

    # Combo values shown to user: "1 - John Smith", "2 - Mathematics"
    student_options = [f"{s[0]} - {s[1]}" for s in students]
    course_options  = [f"{c[0]} - {c[1]}" for c in courses]

    # BUG FIX: These reverse-lookup dicts let autofill_fields() convert
    # a bare name ("John Smith") back to the full option string
    # ("1 - John Smith") that extract_id() can parse correctly.
    student_name_to_option = {s[1]: f"{s[0]} - {s[1]}" for s in students}
    course_name_to_option  = {c[1]: f"{c[0]} - {c[1]}" for c in courses}

    # ── Input form ────────────────────────────────────────────────
    form = tk.Frame(rm, bg=AppTheme.BG, pady=10)
    form.pack(fill="x", padx=AppTheme.PAD)

    tk.Label(form, text="Student", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=0, column=0, sticky="w", padx=6, pady=6)
    student_combo = ttk.Combobox(form, values=student_options, width=AppTheme.ENTRY_W,
                                 font=AppTheme.FONT_ENTRY, state="readonly")
    student_combo.grid(row=0, column=1, padx=6, pady=6)

    tk.Label(form, text="Course", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=1, column=0, sticky="w", padx=6, pady=6)
    course_combo = ttk.Combobox(form, values=course_options, width=AppTheme.ENTRY_W,
                                font=AppTheme.FONT_ENTRY, state="readonly")
    course_combo.grid(row=1, column=1, padx=6, pady=6)

    # ── Helper: extract numeric ID from combo string ──────────────

    def extract_id(combo_value):
        """
        Parses "1 - John Smith" → 1.
        Returns None if the value is empty or malformed.

        This function only works correctly when the combo is set to
        the full "ID - Name" format.  The bug was that autofill_fields()
        was setting the combo to just "John Smith" — fixed below.
        """
        try:
            if not combo_value:
                return None
            return int(combo_value.split(" - ")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Invalid Selection",
                                 "Please select a valid option from the dropdown.")
            return None

    # ── Treeview ──────────────────────────────────────────────────
    tree_frame = tk.Frame(rm, bg=AppTheme.BG)
    tree_frame.pack(fill="both", expand=True, padx=AppTheme.PAD, pady=6)

    tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "Student", "Course", "Date"),
        show="headings",
        style=apply_treeview_style(),
    )
    col_widths = {"ID": 40, "Student": 160, "Course": 160, "Date": 120}
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=col_widths.get(col, 120))

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # ── Autofill (BUG FIX) ────────────────────────────────────────
    def autofill_fields(event):
        """
        ORIGINAL (broken):
            student_combo.set(f"{item[1]}")  # "John Smith" — no ID prefix
            course_combo.set(f"{item[2]}")   # "Mathematics" — no ID prefix

        WHY IT BROKE:
            extract_id("John Smith") → int("John Smith") → ValueError
            So clicking Update after selecting a row silently failed.

        FIX:
            Use the reverse-lookup dicts built from the DB data to convert
            the bare name back to the full "ID - Name" string.
        """
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])["values"]
        # item[1] = "John Smith", item[2] = "Mathematics"

        # Look up the full combo option (e.g. "1 - John Smith")
        student_option = student_name_to_option.get(item[1], "")
        course_option  = course_name_to_option.get(item[2], "")

        # Now set combos in the correct format that extract_id() can parse
        student_combo.set(student_option)
        course_combo.set(course_option)

    tree.bind("<<TreeviewSelect>>", autofill_fields)

    # ── CRUD event handlers ───────────────────────────────────────

    def on_add():
        student_id = extract_id(student_combo.get())
        course_id  = extract_id(course_combo.get())
        if student_id and course_id:
            add_registration(student_id, course_id)
            view_registrations(tree)
            status_var.set("Registration added.")

    def on_update():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a registration row to update.")
            return
        reg_id     = tree.item(selected[0])["values"][0]
        student_id = extract_id(student_combo.get())
        course_id  = extract_id(course_combo.get())
        if student_id and course_id:
            update_registration(reg_id, student_id, course_id)
            view_registrations(tree)
            status_var.set(f"Updated registration ID {reg_id}.")

    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a registration row to delete.")
            return
        reg_id = tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Permanently delete this registration?"):
            delete_registration(reg_id, tree)
            status_var.set(f"Deleted registration ID {reg_id}.")

    # ── Button bar (admin only) ───────────────────────────────────
    if current_user_role == "admin":
        btn_frame = tk.Frame(rm, bg=AppTheme.BG, pady=6)
        btn_frame.pack()
        styled_button(btn_frame, "Add",    on_add,    style="success").pack(side="left", padx=6)
        styled_button(btn_frame, "Update", on_update, style="warning").pack(side="left", padx=6)
        styled_button(btn_frame, "Delete", on_delete, style="danger").pack(side="left", padx=6)

    # ── Filter bar ────────────────────────────────────────────────
    def on_filter():
        name_q   = name_search.real_value().lower()
        course_q = course_search.real_value().lower()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT r.id, s.first_name || ' ' || s.last_name, c.name, r.registration_date "
            "FROM Registrations r "
            "JOIN Students s ON r.student_id = s.id "
            "JOIN Courses  c ON r.course_id  = c.id"
        )
        rows = cursor.fetchall()
        conn.close()

        filtered = [
            r for r in rows
            if name_q in r[1].lower() and course_q in r[2].lower()
        ]
        tree.delete(*tree.get_children())
        for row in filtered:
            tree.insert("", "end", values=row)
        status_var.set(f"Filter results: {len(filtered)} registration(s) found")

    filter_frame = tk.Frame(rm, bg=AppTheme.BG, pady=6)
    filter_frame.pack()

    name_search   = PlaceholderEntry(filter_frame, placeholder="Filter by student name", width=24)
    course_search = PlaceholderEntry(filter_frame, placeholder="Filter by course name",  width=24)
    name_search.pack(side="left", padx=6)
    course_search.pack(side="left", padx=6)
    styled_button(filter_frame, "Filter", on_filter, style="primary", width=10).pack(side="left", padx=4)

    # ── Status bar ────────────────────────────────────────────────
    status_var = tk.StringVar(value="")
    tk.Label(rm, textvariable=status_var, font=AppTheme.FONT_SMALL,
             bg=AppTheme.PANEL, fg=AppTheme.HEADER_TEXT,
             anchor="w", padx=AppTheme.PAD).pack(side="bottom", fill="x")

    # Initial load
    view_registrations(tree)
