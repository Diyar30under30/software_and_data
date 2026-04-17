# =====================================================================
# courses.py  —  Course CRUD + search/sort
# =====================================================================
# CHANGES VS ORIGINAL:
#   1. PlaceholderEntry removed — imported from utils.helpers.
#   2. bubble_sort() BUG FIX: str() wrapping prevents crash on integer
#      columns (same fix applied as in students.py).
#   3. AppTheme + styled_button() for visual consistency.
#   4. apply_treeview_style() for dark Treeview headers.
#   5. Status bar for user feedback after each action.
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

def add_course(name, description):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Courses (name, description) VALUES (?, ?)",
            (name, description),
        )
        conn.commit()
        messagebox.showinfo("Success", "Course added.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def view_courses(tree):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Courses")
    rows = cursor.fetchall()
    conn.close()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)


def delete_course(course_id, tree):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Courses WHERE id=?", (course_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Course deleted.")
        view_courses(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def update_course(course_id, name, description, tree):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Courses SET name=?, description=? WHERE id=?",
            (name, description, course_id),
        )
        conn.commit()
        messagebox.showinfo("Updated", "Course updated.")
        view_courses(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────
# ALGORITHMS
# ─────────────────────────────────────────────────────────────────────

def linear_search(data, query):
    """Case-insensitive substring search across all columns."""
    query = query.lower()
    return [row for row in data if query in " ".join(str(v) for v in row).lower()]


def bubble_sort(data, index):
    """
    Sort rows by column at `index`.
    BUG FIX: str() prevents AttributeError when column value is an int.
    """
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if str(data[j][index]).lower() > str(data[j + 1][index]).lower():
                data[j], data[j + 1] = data[j + 1], data[j]
    return data


# ─────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────

def open_course_management(current_user_role):

    cm = make_window("Course Management", width=620, height=500)
    make_header(cm, "📚 Course Management")

    # ── Input form ────────────────────────────────────────────────
    form = tk.Frame(cm, bg=AppTheme.BG, pady=10)
    form.pack(fill="x", padx=AppTheme.PAD)

    def make_entry(row, label_text):
        tk.Label(form, text=label_text, font=AppTheme.FONT_LABEL,
                 bg=AppTheme.BG, fg=AppTheme.TEXT).grid(
            row=row, column=0, sticky="w", padx=6, pady=5)
        e = tk.Entry(form, font=AppTheme.FONT_ENTRY, width=AppTheme.ENTRY_W,
                     relief="flat", highlightthickness=1,
                     highlightbackground=AppTheme.BORDER, highlightcolor=AppTheme.PRIMARY)
        e.grid(row=row, column=1, padx=6, pady=5)
        return e

    name_entry = make_entry(0, "Course Name")
    desc_entry = make_entry(1, "Description")

    # ── Treeview ──────────────────────────────────────────────────
    tree_frame = tk.Frame(cm, bg=AppTheme.BG)
    tree_frame.pack(fill="both", expand=True, padx=AppTheme.PAD, pady=6)

    tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "Name", "Description"),
        show="headings",
        style=apply_treeview_style(),
    )
    tree.heading("ID",          text="ID");          tree.column("ID",          width=50,  anchor="center")
    tree.heading("Name",        text="Name");        tree.column("Name",        width=180, anchor="center")
    tree.heading("Description", text="Description"); tree.column("Description", width=320, anchor="w")

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # Autofill fields when a row is selected
    def autofill_fields(event):
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])["values"]
            name_entry.delete(0, tk.END); name_entry.insert(0, item[1])
            desc_entry.delete(0, tk.END); desc_entry.insert(0, item[2])

    tree.bind("<<TreeviewSelect>>", autofill_fields)

    # ── CRUD handlers ─────────────────────────────────────────────

    def on_add():
        name = name_entry.get().strip()
        desc = desc_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Field", "Course name is required.")
            return
        add_course(name, desc)
        view_courses(tree)
        status_var.set(f"Added course: {name}")

    def on_update():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a course row to update.")
            return
        course_id = tree.item(selected[0])["values"][0]
        name = name_entry.get().strip()
        desc = desc_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Field", "Course name is required.")
            return
        update_course(course_id, name, desc, tree)
        status_var.set(f"Updated course ID {course_id}")

    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a course row to delete.")
            return
        course_id = tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Permanently delete this course?"):
            delete_course(course_id, tree)
            status_var.set(f"Deleted course ID {course_id}")

    # ── Button bar (admin only) ───────────────────────────────────
    if current_user_role == "admin":
        btn_frame = tk.Frame(cm, bg=AppTheme.BG, pady=6)
        btn_frame.pack()
        styled_button(btn_frame, "Add",    on_add,    style="success").pack(side="left", padx=6)
        styled_button(btn_frame, "Update", on_update, style="warning").pack(side="left", padx=6)
        styled_button(btn_frame, "Delete", on_delete, style="danger").pack(side="left", padx=6)

    # ── Search / Sort bar ─────────────────────────────────────────

    def on_search():
        query = search_entry.real_value()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Courses")
        rows = cursor.fetchall()
        conn.close()
        results = linear_search(rows, query)
        tree.delete(*tree.get_children())
        for row in results:
            tree.insert("", "end", values=row)
        status_var.set(f"Search: {len(results)} course(s) found")

    def on_sort():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Courses")
        rows = cursor.fetchall()
        conn.close()
        sorted_rows = bubble_sort(list(rows), index=1)   # Sort by name (index 1)
        tree.delete(*tree.get_children())
        for row in sorted_rows:
            tree.insert("", "end", values=row)
        status_var.set(f"Sorted {len(sorted_rows)} course(s) by name")

    search_frame = tk.Frame(cm, bg=AppTheme.BG, pady=6)
    search_frame.pack()

    search_entry = PlaceholderEntry(search_frame, placeholder="Search by name / ID", width=26)
    search_entry.pack(side="left", padx=6)
    styled_button(search_frame, "Search",       on_search, style="primary", width=10).pack(side="left", padx=4)
    styled_button(search_frame, "Sort by Name", on_sort,   style="neutral", width=12).pack(side="left", padx=4)

    # ── Status bar ────────────────────────────────────────────────
    status_var = tk.StringVar(value="")
    tk.Label(cm, textvariable=status_var, font=AppTheme.FONT_SMALL,
             bg=AppTheme.PANEL, fg=AppTheme.HEADER_TEXT,
             anchor="w", padx=AppTheme.PAD).pack(side="bottom", fill="x")

    view_courses(tree)
