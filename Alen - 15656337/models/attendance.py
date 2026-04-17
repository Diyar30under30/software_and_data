# =====================================================================
# attendance.py  —  Attendance CRUD + filter
# =====================================================================
# CHANGES VS ORIGINAL:
#   1. PlaceholderEntry removed — imported from utils.helpers.
#   2. AppTheme + styled_button() for visual consistency.
#   3. apply_treeview_style() for dark Treeview headers.
#   4. Filter now uses PlaceholderEntry.real_value() to avoid treating
#      placeholder text ("Search by date...") as a real filter value.
#      Original bug: if you clicked Filter without typing anything,
#      it would filter by the placeholder string and show 0 results.
#   5. Status bar for user feedback.
# =====================================================================

from database import get_connection
from utils.helpers import (
    AppTheme, PlaceholderEntry, apply_treeview_style,
    make_window, make_header, styled_button,
)
from tkinter import messagebox, ttk
import sqlite3
import tkinter as tk
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────
# DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────────────

def add_attendance(student_id, date, status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Attendance (student_id, date, status) VALUES (?, ?, ?)",
            (student_id, date, status),
        )
        conn.commit()
        messagebox.showinfo("Success", "Attendance recorded.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def update_attendance(attendance_id, student_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Attendance SET student_id=?, status=? WHERE id=?",
            (student_id, status, attendance_id),
        )
        conn.commit()
        messagebox.showinfo("Updated", "Attendance record updated.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def delete_attendance(attendance_id, tree):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Attendance WHERE id=?", (attendance_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Attendance record deleted.")
        view_attendance(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def view_attendance(tree):
    """
    Fetches attendance joined with student names.
    The Treeview displays the student's full name instead of their raw ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT a.id, "
        "       s.first_name || ' ' || s.last_name AS student, "
        "       a.date, a.status "
        "FROM Attendance a "
        "JOIN Students s ON a.student_id = s.id"
    )
    rows = cursor.fetchall()
    conn.close()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)


# ─────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────

def open_attendance_management(current_user_role):

    am = make_window("Attendance Management", width=660, height=520)
    make_header(am, "✅ Attendance Management")

    # ── Input form ────────────────────────────────────────────────
    form = tk.Frame(am, bg=AppTheme.BG, pady=10)
    form.pack(fill="x", padx=AppTheme.PAD)

    tk.Label(form, text="Student", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=0, column=0, sticky="w", padx=6, pady=6)

    # Populate student dropdown from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name || ' ' || last_name FROM Students")
    students = cursor.fetchall()
    conn.close()

    student_combo = ttk.Combobox(
        form,
        values=[f"{s[0]} - {s[1]}" for s in students],
        width=AppTheme.ENTRY_W,
        font=AppTheme.FONT_ENTRY,
        state="readonly",
    )
    student_combo.grid(row=0, column=1, padx=6, pady=6)

    tk.Label(form, text="Status", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=1, column=0, sticky="w", padx=6, pady=6)

    status_entry = ttk.Combobox(
        form,
        values=["Present", "Absent", "Excused"],
        width=AppTheme.ENTRY_W,
        font=AppTheme.FONT_ENTRY,
        state="readonly",
    )
    status_entry.set("Absent")   # Sensible default
    status_entry.grid(row=1, column=1, padx=6, pady=6)

    # ── Treeview ──────────────────────────────────────────────────
    tree_frame = tk.Frame(am, bg=AppTheme.BG)
    tree_frame.pack(fill="both", expand=True, padx=AppTheme.PAD, pady=6)

    tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "Student", "Date", "Status"),
        show="headings",
        style=apply_treeview_style(),
    )
    col_widths = {"ID": 40, "Student": 180, "Date": 110, "Status": 90}
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=col_widths.get(col, 120))

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # ── Helper: extract student ID ────────────────────────────────

    def extract_id(combo_value):
        try:
            return int(combo_value.split(" - ")[0]) if combo_value else None
        except (ValueError, IndexError):
            messagebox.showerror("Invalid Selection", "Please select a valid student.")
            return None

    # ── Autofill on row select ────────────────────────────────────
    def autofill_fields(event):
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])["values"]
            # item[0]=id, item[1]="John Smith", item[2]=date, item[3]=status
            # We look up the full combo option from the student name
            for s in students:
                if f"{s[1]}" == item[1]:
                    student_combo.set(f"{s[0]} - {s[1]}")
                    break
            status_entry.set(item[3])

    tree.bind("<<TreeviewSelect>>", autofill_fields)

    # ── CRUD handlers ─────────────────────────────────────────────

    def on_add():
        student_id   = extract_id(student_combo.get())
        current_date = datetime.now().strftime("%Y-%m-%d")   # Auto-fill today's date
        status       = status_entry.get()

        if not student_id:
            return
        if status not in ["Present", "Absent", "Excused"]:
            messagebox.showerror("Invalid Status", "Select Present, Absent, or Excused.")
            return

        add_attendance(student_id, current_date, status)
        view_attendance(tree)
        status_var.set(f"Recorded attendance for student ID {student_id} — {status}")

    def on_update():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select an attendance row to update.")
            return
        attendance_id = tree.item(selected[0])["values"][0]
        student_id    = extract_id(student_combo.get())
        status        = status_entry.get()

        if not student_id:
            return
        if status not in ["Present", "Absent", "Excused"]:
            messagebox.showerror("Invalid Status", "Select Present, Absent, or Excused.")
            return

        update_attendance(attendance_id, student_id, status)
        view_attendance(tree)
        status_var.set(f"Updated attendance ID {attendance_id}")

    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select an attendance row to delete.")
            return
        attendance_id = tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Permanently delete this attendance record?"):
            delete_attendance(attendance_id, tree)
            status_var.set(f"Deleted attendance ID {attendance_id}")

    # ── Button bar (admin only) ───────────────────────────────────
    if current_user_role == "admin":
        btn_frame = tk.Frame(am, bg=AppTheme.BG, pady=6)
        btn_frame.pack()
        styled_button(btn_frame, "Record",  on_add,    style="success").pack(side="left", padx=6)
        styled_button(btn_frame, "Update",  on_update, style="warning").pack(side="left", padx=6)
        styled_button(btn_frame, "Delete",  on_delete, style="danger").pack(side="left", padx=6)

    # ── Filter bar ────────────────────────────────────────────────
    def on_filter():
        """
        BUG FIX: Original used .get() which returned placeholder text
        if the user hadn't typed anything, e.g. "Search by date (YYYY-MM-DD)".
        That string would never match any date → 0 results shown unexpectedly.

        Fix: use .real_value() which returns "" when placeholder is active,
        so an empty filter matches everything (show all rows).
        """
        name_q = name_search.real_value().lower()
        date_q = date_search.real_value()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT a.id, s.first_name || ' ' || s.last_name, a.date, a.status "
            "FROM Attendance a JOIN Students s ON a.student_id = s.id"
        )
        rows = cursor.fetchall()
        conn.close()

        # Both filters are applied with AND logic.
        # Empty string ("") matches every row — so blank filter = show all.
        filtered = [
            r for r in rows
            if name_q in r[1].lower() and date_q in r[2]
        ]
        tree.delete(*tree.get_children())
        for row in filtered:
            tree.insert("", "end", values=row)
        status_var.set(f"Filter results: {len(filtered)} record(s) found")

    filter_frame = tk.Frame(am, bg=AppTheme.BG, pady=6)
    filter_frame.pack()

    name_search = PlaceholderEntry(filter_frame, placeholder="Filter by student name",   width=24)
    date_search = PlaceholderEntry(filter_frame, placeholder="Filter by date YYYY-MM-DD", width=24)
    name_search.pack(side="left", padx=6)
    date_search.pack(side="left", padx=6)
    styled_button(filter_frame, "Filter", on_filter, style="primary", width=10).pack(side="left", padx=4)

    # ── Status bar ────────────────────────────────────────────────
    status_var = tk.StringVar(value="")
    tk.Label(am, textvariable=status_var, font=AppTheme.FONT_SMALL,
             bg=AppTheme.PANEL, fg=AppTheme.HEADER_TEXT,
             anchor="w", padx=AppTheme.PAD).pack(side="bottom", fill="x")

    view_attendance(tree)
