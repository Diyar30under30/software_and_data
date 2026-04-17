# =====================================================================
# teachers.py  —  Teacher CRUD + search/filter
# =====================================================================
# BUG FIXED ▶ DUPLICATE FILTER WIDGETS
#   The original open_teacher_management() defined name_search,
#   subject_search, and the Filter button TWICE — once above the
#   view_teachers(tree) call and again at the very bottom.
#   The second set of widgets was placed in the same grid cells (row=7)
#   as the first, so they stacked invisibly on top of each other.
#   Every click on "Filter" fired on_filter() twice, and the layout
#   had mystery invisible widgets consuming memory.
#   Fix: define and place the filter widgets exactly once.
#
# OTHER CHANGES:
#   1. Uses AppTheme + styled_button() for visual consistency.
#   2. apply_treeview_style() gives the table a dark header.
#   3. Subject dropdown repopulated with courses from the DB.
#   4. Status bar shows feedback after each action.
# =====================================================================

from database import get_connection
from utils.helpers import (
    AppTheme, PlaceholderEntry, apply_treeview_style,
    make_window, make_header, styled_button,
)
from tkinter import messagebox, ttk
import sqlite3
import tkinter as tk
import re


# ─────────────────────────────────────────────────────────────────────
# DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────────────

def add_teacher(first_name, last_name, subject, email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Teachers (first_name, last_name, subject, email) VALUES (?, ?, ?, ?)",
            (first_name, last_name, subject, email),
        )
        conn.commit()
        messagebox.showinfo("Success", "Teacher added.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def view_teachers(tree):
    """Fetches all teachers and populates the Treeview."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Teachers")
    rows = cursor.fetchall()
    conn.close()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)


def delete_teacher(teacher_id, tree):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Teachers WHERE id=?", (teacher_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Teacher deleted.")
        view_teachers(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def update_teacher(teacher_id, first_name, last_name, subject, email, tree):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Teachers SET first_name=?, last_name=?, subject=?, email=? WHERE id=?",
            (first_name, last_name, subject, email, teacher_id),
        )
        conn.commit()
        messagebox.showinfo("Updated", "Teacher updated.")
        view_teachers(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def is_duplicate_teacher(first_name, last_name, email):
    """Returns True if a teacher with the same name AND email already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM Teachers WHERE first_name=? AND last_name=? AND email=?",
        (first_name, last_name, email),
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def is_valid_email(email):
    """
    Validates email format using a regular expression.
    Pattern requires: localpart @ domain . tld (2+ chars)
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ─────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────

def open_teacher_management(current_user_role):
    """
    Opens the Teacher Management window.

    Layout:
        1. Dark header
        2. Input form (First / Last / Subject dropdown / Email)
        3. Admin-only CRUD buttons
        4. Themed Treeview
        5. Filter bar (name + subject) ← defined ONCE (bug fix)
        6. Status bar
    """
    tm = make_window("Teacher Management", width=700, height=580)
    make_header(tm, "🧑‍🏫 Teacher Management")

    # ── Input form ────────────────────────────────────────────────
    form = tk.Frame(tm, bg=AppTheme.BG, pady=10)
    form.pack(fill="x", padx=AppTheme.PAD)

    def lbl(text, row):
        tk.Label(form, text=text, font=AppTheme.FONT_LABEL,
                 bg=AppTheme.BG, fg=AppTheme.TEXT).grid(
            row=row, column=0, sticky="w", padx=6, pady=4)

    def ent(row):
        e = tk.Entry(form, font=AppTheme.FONT_ENTRY, width=AppTheme.ENTRY_W,
                     relief="flat", highlightthickness=1,
                     highlightbackground=AppTheme.BORDER, highlightcolor=AppTheme.PRIMARY)
        e.grid(row=row, column=1, padx=6, pady=4)
        return e

    lbl("First Name", 0); fn    = ent(0)
    lbl("Last Name",  1); ln    = ent(1)
    lbl("Email",      3); email = ent(3)

    # Subject is a Combobox populated from Courses table
    lbl("Subject", 2)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Courses")
    courses = [c[0] for c in cursor.fetchall()]
    conn.close()

    subj = ttk.Combobox(form, values=courses, width=AppTheme.ENTRY_W - 2,
                        font=AppTheme.FONT_ENTRY)
    subj.grid(row=2, column=1, padx=6, pady=4)

    # ── Treeview ──────────────────────────────────────────────────
    tree_frame = tk.Frame(tm, bg=AppTheme.BG)
    tree_frame.pack(fill="both", expand=True, padx=AppTheme.PAD, pady=6)

    tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "First", "Last", "Subject", "Email"),
        show="headings",
        style=apply_treeview_style(),
    )
    col_widths = {"ID": 40, "First": 100, "Last": 100, "Subject": 120, "Email": 200}
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=col_widths.get(col, 120))

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # ── Autofill ──────────────────────────────────────────────────
    def autofill_fields(event):
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])["values"]
            fn.delete(0, tk.END);    fn.insert(0, item[1])
            ln.delete(0, tk.END);    ln.insert(0, item[2])
            subj.set(item[3])
            email.delete(0, tk.END); email.insert(0, item[4])

    tree.bind("<<TreeviewSelect>>", autofill_fields)

    # ── CRUD event handlers ───────────────────────────────────────

    def on_add():
        first_name  = fn.get().strip()
        last_name   = ln.get().strip()
        subject     = subj.get().strip()
        email_value = email.get().strip()

        if not first_name.isalpha() or not last_name.isalpha():
            messagebox.showerror("Invalid Input", "Names must contain only letters.")
            return
        if not is_valid_email(email_value):
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return
        if is_duplicate_teacher(first_name, last_name, email_value):
            messagebox.showerror("Duplicate", "This teacher already exists in the database.")
            return

        add_teacher(first_name, last_name, subject, email_value)
        view_teachers(tree)
        status_var.set(f"Added teacher: {first_name} {last_name}")

    def on_update():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a teacher row to update.")
            return
        teacher_id  = tree.item(selected[0])["values"][0]
        first_name  = fn.get().strip()
        last_name   = ln.get().strip()
        subject     = subj.get().strip()
        email_value = email.get().strip()

        if not first_name.isalpha() or not last_name.isalpha():
            messagebox.showerror("Invalid Input", "Names must contain only letters.")
            return
        if not is_valid_email(email_value):
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return

        update_teacher(teacher_id, first_name, last_name, subject, email_value, tree)
        status_var.set(f"Updated teacher ID {teacher_id}")

    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a teacher row to delete.")
            return
        teacher_id = tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Permanently delete this teacher?"):
            delete_teacher(teacher_id, tree)
            status_var.set(f"Deleted teacher ID {teacher_id}")

    # ── Button bar (admin only) ───────────────────────────────────
    if current_user_role == "admin":
        btn_frame = tk.Frame(tm, bg=AppTheme.BG, pady=6)
        btn_frame.pack()
        styled_button(btn_frame, "Add",    on_add,    style="success").pack(side="left", padx=6)
        styled_button(btn_frame, "Update", on_update, style="warning").pack(side="left", padx=6)
        styled_button(btn_frame, "Delete", on_delete, style="danger").pack(side="left", padx=6)

    # ── Filter bar ────────────────────────────────────────────────
    # BUG FIX: this block existed TWICE in the original (once before
    # view_teachers() and once at the very bottom).  Now it is here ONCE.

    def on_filter():
        """
        Fetches all teachers and filters in-memory by name and subject.
        Both filters are applied together (AND logic).
        """
        name_q    = name_search.real_value().lower()
        subject_q = subject_search.real_value().lower()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Teachers")
        rows = cursor.fetchall()
        conn.close()

        filtered = [
            row for row in rows
            # row[1] = first_name, row[2] = last_name, row[3] = subject
            if name_q    in (row[1] + " " + row[2]).lower()
            and subject_q in row[3].lower()
        ]

        tree.delete(*tree.get_children())
        for row in filtered:
            tree.insert("", "end", values=row)
        status_var.set(f"Filter results: {len(filtered)} teacher(s) found")

    filter_frame = tk.Frame(tm, bg=AppTheme.BG, pady=6)
    filter_frame.pack()

    # PlaceholderEntry from utils.helpers — no local copy needed
    name_search    = PlaceholderEntry(filter_frame, placeholder="Filter by name",    width=22)
    subject_search = PlaceholderEntry(filter_frame, placeholder="Filter by subject", width=22)
    name_search.pack(side="left", padx=6)
    subject_search.pack(side="left", padx=6)
    styled_button(filter_frame, "Filter", on_filter, style="primary", width=10).pack(side="left", padx=4)

    # ── Status bar ────────────────────────────────────────────────
    status_var = tk.StringVar(value="")
    tk.Label(tm, textvariable=status_var, font=AppTheme.FONT_SMALL,
             bg=AppTheme.PANEL, fg=AppTheme.HEADER_TEXT,
             anchor="w", padx=AppTheme.PAD).pack(side="bottom", fill="x")

    # Initial table load
    view_teachers(tree)
