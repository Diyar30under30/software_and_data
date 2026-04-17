# =====================================================================
# students.py  —  Student CRUD + search/sort/pagination
# =====================================================================
# CHANGES VS ORIGINAL:
#   1. PlaceholderEntry removed — imported from utils.helpers (single source).
#   2. bubble_sort() BUG FIX: original called .lower() directly on data
#      values which crashes when a value is an integer (e.g. the age or ID
#      column).  Fixed with str(value) conversion before comparison.
#   3. All widgets use AppTheme colors and fonts for visual consistency.
#   4. Button frame uses styled_button() — no more bare tk.Button() calls.
#   5. Treeview uses apply_treeview_style() for the themed header + rows.
#   6. Status bar at the bottom shows live row count feedback.
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

def add_student(first_name, last_name, age):
    """Inserts a new row into the Students table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Students (first_name, last_name, age) VALUES (?, ?, ?)",
            (first_name, last_name, age),
        )
        conn.commit()
        messagebox.showinfo("Success", "Student added successfully.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def view_students(tree, page=1, rows_per_page=10):
    """
    Fetches all students, applies pagination, and populates the Treeview.

    Pagination math:
        page=1, rows_per_page=10  →  start=0,  end=10  →  rows[0:10]
        page=2, rows_per_page=10  →  start=10, end=20  →  rows[10:20]

    Returns the total row count so callers can calculate the page count.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students")
    all_rows = cursor.fetchall()   # Fetch everything; slice in Python
    conn.close()

    # ── Pagination slice ─────────────────────────────────────────
    start = (page - 1) * rows_per_page
    end   = start + rows_per_page
    page_rows = all_rows[start:end]   # Only the rows for this page

    # ── Refresh Treeview ─────────────────────────────────────────
    tree.delete(*tree.get_children())   # Clear existing rows first
    for row in page_rows:
        tree.insert("", "end", values=row)

    return len(all_rows)   # Caller needs total count for page label


def delete_student(student_id, tree):
    """Deletes a student row by primary key and refreshes the table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Students WHERE id=?", (student_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Student deleted.")
        view_students(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


def update_student(student_id, first_name, last_name, age, tree):
    """Updates first_name, last_name, and age for a given student ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Students SET first_name=?, last_name=?, age=? WHERE id=?",
            (first_name, last_name, age, student_id),
        )
        conn.commit()
        messagebox.showinfo("Updated", "Student updated.")
        view_students(tree)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────
# ALGORITHMS
# ─────────────────────────────────────────────────────────────────────

def linear_search(data, query):
    """
    Case-insensitive search across all columns of every row.
    Converts each value to string so integer columns (ID, age) are
    also searched without raising a TypeError.
    """
    query = query.lower()
    # str(value) handles integers and None values safely
    return [row for row in data if query in " ".join(str(v) for v in row).lower()]


def bubble_sort(data, index):
    """
    Sorts rows by the value at the given column index.

    BUG FIX — original code:
        if data[j][index].lower() > data[j+1][index].lower()
        ↑ This crashes with AttributeError when data[j][index] is an int
          (e.g., sorting by ID=0 or Age=3).

    Fix:
        Convert to str() before calling .lower() so both strings and
        integers are handled uniformly.
    """
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            # str() ensures integers don't raise AttributeError
            if str(data[j][index]).lower() > str(data[j + 1][index]).lower():
                data[j], data[j + 1] = data[j + 1], data[j]   # Swap
    return data


# ─────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────

def open_student_management(current_user_role):
    """
    Opens the Student Management window.

    Layout (top to bottom):
        1. Dark header bar
        2. Input form (First Name / Last Name / Age)
        3. Admin-only CRUD buttons
        4. Themed Treeview table
        5. Pagination controls
        6. Search + Sort bar
        7. Status bar (live row count)
    """
    sm = make_window("Student Management", width=680, height=620)
    make_header(sm, "👤 Student Management")

    # ── Input frame ───────────────────────────────────────────────
    # grid() layout keeps labels left-aligned and entries right-aligned.
    input_frame = tk.Frame(sm, bg=AppTheme.BG, pady=10)
    input_frame.pack(fill="x", padx=AppTheme.PAD)

    tk.Label(input_frame, text="First Name", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=0, column=0, sticky="w", padx=6, pady=4)
    fn = tk.Entry(input_frame, font=AppTheme.FONT_ENTRY, width=AppTheme.ENTRY_W,
                  relief="flat", highlightthickness=1,
                  highlightbackground=AppTheme.BORDER, highlightcolor=AppTheme.PRIMARY)
    fn.grid(row=0, column=1, padx=6, pady=4)

    tk.Label(input_frame, text="Last Name", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=1, column=0, sticky="w", padx=6, pady=4)
    ln = tk.Entry(input_frame, font=AppTheme.FONT_ENTRY, width=AppTheme.ENTRY_W,
                  relief="flat", highlightthickness=1,
                  highlightbackground=AppTheme.BORDER, highlightcolor=AppTheme.PRIMARY)
    ln.grid(row=1, column=1, padx=6, pady=4)

    tk.Label(input_frame, text="Age", font=AppTheme.FONT_LABEL,
             bg=AppTheme.BG, fg=AppTheme.TEXT).grid(row=2, column=0, sticky="w", padx=6, pady=4)
    age = tk.Entry(input_frame, font=AppTheme.FONT_ENTRY, width=AppTheme.ENTRY_W,
                   relief="flat", highlightthickness=1,
                   highlightbackground=AppTheme.BORDER, highlightcolor=AppTheme.PRIMARY)
    age.grid(row=2, column=1, padx=6, pady=4)

    # ── Treeview ──────────────────────────────────────────────────
    tree_frame = tk.Frame(sm, bg=AppTheme.BG)
    tree_frame.pack(fill="both", expand=True, padx=AppTheme.PAD, pady=6)

    style_name = apply_treeview_style()   # Apply the themed style once
    tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "First", "Last", "Age"),
        show="headings",
        style=style_name,               # Use our custom dark-header style
    )
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=140)

    # Scrollbar — attached to tree and packed to the right
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # ── Validation helpers ────────────────────────────────────────

    def validate_text(value):
        """Only allow alphabetic characters in name fields."""
        return value.isalpha()

    def is_duplicate(first_name, last_name):
        """Check if a student with the same full name already exists."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Students WHERE first_name=? AND last_name=?",
            (first_name, last_name),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    # ── Pagination state ──────────────────────────────────────────
    # IntVar allows the label and buttons to read/write the same value.
    current_page  = tk.IntVar(value=1)
    rows_per_page = tk.IntVar(value=10)

    def update_table():
        """Refresh the Treeview with the current page and rows_per_page."""
        total_rows  = view_students(tree, current_page.get(), rows_per_page.get())
        total_pages = max(1, (total_rows + rows_per_page.get() - 1) // rows_per_page.get())
        pagination_label.config(
            text=f"Page {current_page.get()} of {total_pages}"
        )
        # Status bar shows live count — useful feedback
        status_var.set(f"Total students: {total_rows}")

    def next_page():
        total_rows  = view_students(tree, current_page.get(), rows_per_page.get())
        total_pages = max(1, (total_rows + rows_per_page.get() - 1) // rows_per_page.get())
        if current_page.get() < total_pages:
            current_page.set(current_page.get() + 1)
            update_table()
        else:
            messagebox.showinfo("Last Page", "You are already on the last page.")

    def prev_page():
        if current_page.get() > 1:
            current_page.set(current_page.get() - 1)
            update_table()

    # ── Autofill on row select ────────────────────────────────────
    def autofill_fields(event):
        """
        When the user clicks a row in the table, populate the form fields
        with that row's values so they can edit without retyping everything.
        """
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])["values"]
            fn.delete(0, tk.END);  fn.insert(0, item[1])
            ln.delete(0, tk.END);  ln.insert(0, item[2])
            age.delete(0, tk.END); age.insert(0, item[3])

    tree.bind("<<TreeviewSelect>>", autofill_fields)

    # ── CRUD event handlers ───────────────────────────────────────

    def on_add():
        first_name = fn.get().strip()
        last_name  = ln.get().strip()
        age_value  = age.get().strip()

        if not validate_text(first_name) or not validate_text(last_name):
            messagebox.showerror("Invalid Input", "Names must contain only letters.")
            return
        if not age_value.isdigit() or not (6 <= int(age_value) <= 20):
            messagebox.showerror("Invalid Age", "Age must be a number between 6 and 20.")
            return
        if is_duplicate(first_name, last_name):
            messagebox.showerror("Duplicate", "A student with this name already exists.")
            return

        add_student(first_name, last_name, int(age_value))
        update_table()

    def on_update():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a student row to update.")
            return
        student_id = tree.item(selected[0])["values"][0]
        first_name = fn.get().strip()
        last_name  = ln.get().strip()
        age_value  = age.get().strip()

        if not validate_text(first_name) or not validate_text(last_name):
            messagebox.showerror("Invalid Input", "Names must contain only letters.")
            return
        if not age_value.isdigit() or not (6 <= int(age_value) <= 20):
            messagebox.showerror("Invalid Age", "Age must be a number between 6 and 20.")
            return

        update_student(student_id, first_name, last_name, int(age_value), tree)
        update_table()

    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a student row to delete.")
            return
        student_id = tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Permanently delete this student?"):
            delete_student(student_id, tree)
            update_table()

    # ── Button bar (admin only) ───────────────────────────────────
    if current_user_role == "admin":
        btn_frame = tk.Frame(sm, bg=AppTheme.BG, pady=6)
        btn_frame.pack()
        styled_button(btn_frame, "Add",    on_add,    style="success").pack(side="left", padx=6)
        styled_button(btn_frame, "Update", on_update, style="warning").pack(side="left", padx=6)
        styled_button(btn_frame, "Delete", on_delete, style="danger").pack(side="left", padx=6)

    # ── Pagination bar ────────────────────────────────────────────
    page_frame = tk.Frame(sm, bg=AppTheme.BG, pady=6)
    page_frame.pack()

    styled_button(page_frame, "◀ Prev", prev_page, style="neutral", width=8).pack(side="left", padx=4)
    pagination_label = tk.Label(page_frame, text="", font=AppTheme.FONT_SMALL,
                                bg=AppTheme.BG, fg=AppTheme.TEXT)
    pagination_label.pack(side="left", padx=8)
    styled_button(page_frame, "Next ▶", next_page, style="neutral", width=8).pack(side="left", padx=4)

    tk.Label(page_frame, text="Rows/page:", font=AppTheme.FONT_SMALL,
             bg=AppTheme.BG, fg=AppTheme.MUTED).pack(side="left", padx=(12, 4))
    rows_entry = tk.Entry(page_frame, textvariable=rows_per_page, width=4,
                          font=AppTheme.FONT_SMALL, relief="flat",
                          highlightthickness=1, highlightbackground=AppTheme.BORDER)
    rows_entry.pack(side="left")
    styled_button(page_frame, "Apply", update_table, style="neutral", width=6).pack(side="left", padx=4)

    # ── Search / Sort bar ─────────────────────────────────────────

    def on_search():
        """
        Fetches all rows from DB, then uses linear_search() to filter
        client-side.  Results replace the Treeview contents.
        """
        query = search_entry.real_value()   # real_value() skips placeholder text
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Students")
        rows = cursor.fetchall()
        conn.close()
        results = linear_search(rows, query)
        tree.delete(*tree.get_children())
        for row in results:
            tree.insert("", "end", values=row)
        status_var.set(f"Search results: {len(results)} student(s) found")

    def on_sort():
        """Sort all students by first name using bubble_sort()."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Students")
        rows = cursor.fetchall()
        conn.close()
        sorted_rows = bubble_sort(list(rows), index=1)   # index 1 = first_name
        tree.delete(*tree.get_children())
        for row in sorted_rows:
            tree.insert("", "end", values=row)
        status_var.set(f"Sorted {len(sorted_rows)} student(s) by first name")

    search_frame = tk.Frame(sm, bg=AppTheme.BG, pady=6)
    search_frame.pack()

    # PlaceholderEntry imported from utils.helpers — no local copy needed
    search_entry = PlaceholderEntry(search_frame, placeholder="Search by name / age / ID", width=28)
    search_entry.pack(side="left", padx=6)
    styled_button(search_frame, "Search",       on_search, style="primary", width=10).pack(side="left", padx=4)
    styled_button(search_frame, "Sort by Name", on_sort,   style="neutral", width=12).pack(side="left", padx=4)

    # ── Status bar ────────────────────────────────────────────────
    # Thin strip at the bottom — gives live feedback on actions.
    status_var = tk.StringVar(value="")
    status_bar = tk.Label(sm, textvariable=status_var, font=AppTheme.FONT_SMALL,
                          bg=AppTheme.PANEL, fg=AppTheme.HEADER_TEXT,
                          anchor="w", padx=AppTheme.PAD)
    status_bar.pack(side="bottom", fill="x")

    # Initial table load
    update_table()
